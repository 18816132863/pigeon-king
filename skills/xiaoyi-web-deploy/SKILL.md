---
name: xiaoyi-web-deploy
description: 部署网页应用到云服务器中。当用户需要部署网页应用时，使用本 Skill。
---

## 部署上线

- ⚠️ **部署前必须询问用户确认**，得到明确同意后再执行打包和部署操作。
- ⚠️ **部署前必须在 AipexBase 创建一个 BaaS 应用**。如果之前没有创建过 AipexBase BaaS 应用，我们需要首先创建一个不含任何表格的 BaaS 应用；如果之前创建过，忽略这一条。
- 要注意让你部署哪个网页应用。每个网页应用都会绑定一个 BaaS 应用，会有各自的 `appId`。不要搞混 `appId`。
- ⚠️ 入口文件**必须**是 `index.html`。首先检查该文件是否存在。若不存在，需要确定哪个 HTML 文件为入口文件，然后将改文件重命名为 `index.html`。如果难以确认，可向用户提问。

### 创建 BaaS 应用（不含任何表格）

针对当前的网页应用，首先要确认之前是否创建过**相应**的 AipexBase BaaS 应用。若无，我们需要首先创建一个不含任何表格的 BaaS 应用；若有，不需要重新创建。注意不要和其他网页应用对应的 AipexBase BaaS 应用搞混。

#### 配置文件说明

| 配置文件 | 位置 | 说明 |
|---------|------|------|
| **全局配置** `config.json` | 本 skill(`xiaoyi-web-deploy/`) 目录下 | 包含 `baseUrl`，可以用该文件中的默认 `baseUrl` |
| **项目配置** `baas-config.json` | 项目目录下 | 新建应用时从全局配置复制，批量创建后添加 `apiKey` 和 `appId`；迭代开发时直接使用 |

检查项目目录下的 `baas-config.json`：

- **不存在或缺少 `apiKey`** → 新建应用
- **存在且包含 `apiKey`** → 迭代开发

#### 初始化步骤

**步骤 1：检查并初始化全局配置**

读取 `<skill目录>/config.json`，检查 `baseUrl` 是否已配置。

**步骤 2：项目配置**

```bash
cd <项目目录，建议放到 /tmp/时间戳/项目名称 目录下>
cp <当前skill目录>/config.json ./baas-config.json
```

#### 新建应用流程

假如你只想创建一个空 BaaS 应用（不含任何表格），你可以使用下面的方法进行创建（需要用到 `<skill 目录>/scripts/baas.py` 脚本）：

```bash
python3 <本 skill 目录>/scripts/baas.py --x-api-type manageApplication --content - <<'EOF' 
{
  "name": "应用名称"
}
EOF
```

**注**：
- python 环境已配置，无需安装任何 python 包。如果遇到 `requests` 包未安装的错误，你需要换成安装了 `requests` 包的 Python 环境，比如修改 `PYTHONPATH` 环境变量。
- 创建 BaaS 应用（不含表格）时 `--x-api-type` **必须** 为 `manageApplication`

#### 更新 baas-config.json

BaaS 应用创建成功后，使用 Edit 工具添加返回的 `apiKey` 和 `appId`。

### 检查入口文件

入口文件**必须**是 `index.html`。首先检查该文件是否存在。若不存在，需要确定哪个 HTML 文件为入口文件，然后将改文件重命名为 `index.html`。如果难以确认，可向用户提问。

### 打包策略

根据项目类型选择对应的打包方式：

**纯 HTML 项目（无构建步骤）**：

```bash
cd <项目目录>
zip -r project.zip . -x "node_modules/*" -x ".git/*" -x "*.zip"
```

**Vue/React 等需要构建的项目**：

```bash
cd <项目目录>
# 1. 执行构建
npm run build  # 或 yarn build

cd dist   # 或 cd build
zip -r ../project.zip .
```

### 将 zip 包上传至小艺文件存储服务

将上述的 zip 包上传到小艺 OBS。优先使用 `<本 skill 目录>/scripts/upload_file.py`:

```bash
python3 <本 skill 目录>/scripts/upload_file.py <project.zip 路径>
```

上传成功后会返回一个 URL（命名为 `xiaoyiFileUrl`）。这是一个临时 URL。每次重新部署需要重新上传新的 zip 包获得新的 URL。

**注意**：不要尝试把文件转成 base64 上传。无需使用 skill-execute 来上传文件。

### 执行部署

**cURL 示例**：

```bash
python3 <本 skill 目录>/scripts/baas.py --x-api-type deploy --content - <<'EOF' 
{
  "appUrl": <xiaoyiFileUrl>,
  "apiKey": <apiKey>,
  "appId": <appId>
}
EOF
```

**注意**：
- 此接口使用 `apiKey` 进行认证。`apiKey`、`appId` 需要从项目目录中的 `baas-config.json` 中获取。
- 部署时的 `--x-api-type` **必须**是 `deploy`

部署成功后返回：

```json
{
  "code": 0,
  "data": {
    "url": "<部署 URL>"
  },
  "message": "ok",
  "success": true
}
```

### 输出
部署后的 URL 展示给用户。需要把 URL 渲染成可以点击的形式，比如

```markdown
[链接文字](<部署 URL>)
```

并且提醒用户出于合规考虑，这只是一个临时 URL，预览时间为 6 小时。6 小时后需要重新部署。
提醒用户永久域名需要进行 IPC 备案（中国工业和信息化部对境内网站实施的一项基础管理制度），需要用户自行备案。

**注意**：**每次**展示这个部署 URL 均需要将其渲染成可以点击的形式。

## 提醒

- 如果用户想要通过你直接登录部署的网站或云数据库，你要提醒用户要通过前端网页来登录。