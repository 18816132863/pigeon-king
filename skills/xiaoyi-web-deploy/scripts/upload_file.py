import requests
import os
import hashlib
import sys

def read_xiaoyienv():
    """
    读取 ~/.openclaw/.xiaoyienv 文件并返回键值对字典。
    """
    file_path = os.path.expanduser("~/.openclaw/.xiaoyienv")
    env_dict = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # 去除行首尾的空白字符和换行符
                line = line.strip()
                # 跳过空行和以 # 开头的注释行
                if not line or line.startswith('#'):
                    continue
                # 确保行中包含等号
                if '=' in line:
                    # 只在第一个等号处分割，防止 value 中包含等号
                    key, value = line.split('=', 1)
                    env_dict[key.strip()] = value.strip()

    except FileNotFoundError:
        print(f"提示: 未找到文件 {file_path}")
    except Exception as e:
        print(f"读取文件时发生错误: {e}")

    return env_dict

def calculate_sha256(file_path):
    """计算文件的 SHA256 哈希值"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def upload_file(file_path, object_type="TEMPORARY_MATERIAL_DOC"):
    """
    将本地文件上传到小艺文件存储服务（三阶段上传：prepare → upload → complete）

    Args:
        file_path: 本地文件路径
        object_type: 文件类型（默认 TEMPORARY_MATERIAL_DOC）

    Returns:
        fileUrl
    """
    try:
        # 校验文件存在
        if not os.path.isfile(file_path):
            print(f'❌ 文件不存在：{file_path}')
            return None

        # 读取并校验配置
        config = read_xiaoyienv()

        required_keys = ['PERSONAL-API-KEY', 'PERSONAL-UID']
        check_result = True

        for key in required_keys:
            if key not in config:
                print(f'❌ key "{key}" 不存在：失败...')
                check_result = False

        if not check_result:
            return None

        base_url = config['SERVICE_URL']

        # 准备文件信息
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_sha256 = calculate_sha256(file_path)
        uid = config['PERSONAL-UID']

        # 公共请求头
        common_headers = {
            'Content-Type': 'application/json',
            'x-uid': uid,
            'x-api-key': config['PERSONAL-API-KEY'],
            'x-request-from': 'openclaw',
        }

        # ── 阶段 1: Prepare ──────────────────────────────────────────────────────
        prepare_url = f'{base_url}/osms/v1/file/manager/prepare'

        prepare_payload = {
            'objectType': object_type,
            'fileName': file_name,
            'fileSha256': file_sha256,
            'fileSize': file_size,
            'fileOwnerInfo': {
                'uid': uid,
                'teamId': uid,
            },
            'useEdge': False,
        }

        prepare_resp = requests.post(
            prepare_url,
            headers=common_headers,
            json=prepare_payload,
            timeout=30
        )

        if prepare_resp.status_code != 200:
            print(f'❌ Prepare 请求失败: HTTP {prepare_resp.status_code}')
            print(f'❌ 响应内容: {prepare_resp.text}')
            return None

        prepare_data = prepare_resp.json()

        # 部分服务器返回 code 字段，"0" 为成功
        if 'code' in prepare_data and prepare_data['code'] != '0':
            print(f'❌ Prepare 失败: {prepare_data.get("desc", "未知错误")}')
            return None

        object_id = prepare_data.get('objectId')
        draft_id = prepare_data.get('draftId')
        upload_infos = prepare_data.get('uploadInfos', [])

        if not object_id or not draft_id or not upload_infos:
            print(f'❌ Prepare 响应缺少必要字段: objectId={object_id}, draftId={draft_id}')
            return None

        upload_info = upload_infos[0]
        upload_url = upload_info['url']
        upload_method = upload_info.get('method', 'PUT').upper()
        upload_headers = upload_info.get('headers', {'Content-Type': 'application/octet-stream'})

        with open(file_path, 'rb') as f:
            file_data = f.read()

        upload_resp = requests.request(
            method=upload_method,
            url=upload_url,
            headers=upload_headers,
            data=file_data,
            timeout=120
        )

        if upload_resp.status_code not in (200, 204):
            print(f'❌ 文件上传失败: HTTP {upload_resp.status_code}')
            return None

        # ── 阶段 3: Complete ─────────────────────────────────────────────────────
        complete_url = f'{base_url}/osms/v1/file/manager/completeAndQuery'

        complete_payload = {
            'objectId': object_id,
            'draftId': draft_id,
        }

        complete_resp = requests.post(
            complete_url,
            headers=common_headers,
            json=complete_payload,
            timeout=30
        )

        if complete_resp.status_code != 200:
            print(f'❌ Complete 请求失败: HTTP {complete_resp.status_code}')
            return None

        complete_data = complete_resp.json()

        # 从 completeAndQuery 响应中直接获取文件下载 URL
        file_url = complete_data.get('fileDetailInfo', {}).get('url', '')

        return file_url

    except requests.exceptions.Timeout:
        print('❌ 请求超时')
        return None
    except requests.exceptions.ConnectionError as e:
        print(f'❌ 连接失败: {e}')
        return None
    except Exception as e:
        print(f'❌ 上传异常: {e}')
        import traceback
        traceback.print_exc()
        return None

def main():
    print(upload_file(sys.argv[1]))

if __name__ == '__main__':
    main()