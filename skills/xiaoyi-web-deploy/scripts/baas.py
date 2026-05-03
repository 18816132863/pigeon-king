import os
import uuid
from typing import Optional
import json
import argparse

import requests

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
    

def baas_api_call(
        x_api_type: str, 
        content: Optional[str] = None,
        content_file_path: Optional[str] = None,
        x_skill_id: str = 'web_deploy'
    ) -> str:
    if content is None and content_file_path is None:
        return "错误：`content` 和 `content_file_path` 至少一个不能为 `None`"
    if content is not None:
        try:
            content_json = json.loads(content)
        except json.JSONDecodeError as e:
            return(f"解析 `content` 失败: {e}")
    else:
        try:
            with open(content_file_path, 'r', encoding='utf-8') as f:
                content_json = json.load(f)
        except FileNotFoundError:
            return f"文件不存在，请检查路径: {content_file_path}"
        except json.JSONDecodeError:
            return f"JSON格式错误，请检查文件内容: {content_file_path}"
    
    env_dict = read_xiaoyienv()
    base_url = env_dict.get('SERVICE_URL', '')
    x_request_from = 'openclaw'
    x_hag_trace_id = str(uuid.uuid4())
    x_uid = env_dict.get('PERSONAL-UID', '')
    x_api_key = env_dict.get('PERSONAL-API-KEY', '')

    api_url = f'{base_url}/celia-claw/v1/rest-api/skill/execute'
    headers = {
        'Content-Type': 'application/json',
        'x-api-type': x_api_type,
        'x-skill-id': x_skill_id,
        'x-hag-trace-id': x_hag_trace_id,
        'x-uid': x_uid,
        'x-api-key': x_api_key,
        'x-request-from': x_request_from,
    }
    payload = {
        "actions": [
            {
                "actionExecutorTask": {
                    "actionName": "baasApi",
                    "content": content_json,
                    "pluginId": "abf9388fed6b4df89daac71be85fc62c",
                    "replyCard": False
                },
                "actionSn": "81ef5ac1b5e74e85b90832503ea34a07"
            }
        ],
        "endpoint": {
            "countryCode": "",
            "device": {
                "deviceId": "5682d99dbb90973b775b7e9bf774ff9f",
                "phoneType": "2in1",
                "prdVer": "11.6.2.202"
            }
        },
        "session": {
            "interactionId": "0",
            "isNew": False,
            "sessionId": "xxx"
        },
        "utterance": {
            "original": "",
            "type": "text"
        },
        "version": "1.0"
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=120, verify=False, stream=False)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return f"❌ Error: Request timed out (120s)"
    except requests.exceptions.RequestException as e:
        return f"❌ Error: {e}"
    except Exception as e:
        return f"❌ Error: {e}"
    return response.text


def main():
    parser = argparse.ArgumentParser(description="BaaS APIs")
    parser.add_argument("--x-api-type", required=True, help="type of the api")
    parser.add_argument("--content", default=None)
    parser.add_argument("--content-file-path", default=None)
    args = parser.parse_args()
    rst = baas_api_call(
        x_api_type=args.x_api_type,
        content=args.content,
        content_file_path=args.content_file_path
    )
    print(rst)

if __name__ == '__main__':
    main()