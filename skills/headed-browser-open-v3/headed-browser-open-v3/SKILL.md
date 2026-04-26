---
name: headed-browser-open-v3
description: 使用有头浏览器(headed browser)打开网页，通过CDP协议进行元素点击和自动化操作。V3优化版：简化架构，保留核心功能（协议拦截、元素操作、截图），适用于复杂网页场景，特别是需要处理App唤起提示或特殊渲染的页面。
type: skill
tools: [exec, browser]
---

# Headed Browser Open Skill V3

## 概述

本 Skill 提供通过 CDP (Chrome DevTools Protocol) 控制有头浏览器的能力，适用于需要模拟真实用户环境、处理 App 唤起弹窗、操作复杂交互页面的场景。

**核心特性：**
- 真实 Chrome 浏览器（非 headless），更接近真实用户环境
- CDP 协议控制，支持元素查找、点击、输入、截图
- 自动拦截外部协议弹窗（weixin://, taobao:// 等）
- Xvfb 虚拟显示支持，无需物理显示器

---

## 使用指南

### 何时使用本 Skill

| 场景 | 是否适用 | 说明 |
|------|---------|------|
| 需要模拟真实浏览器环境 | ✅ | 有头浏览器更接近真实用户 |
| 网站触发 App 唤起弹窗 | ✅ | 自动拦截外部协议 |
| 复杂交互页面（登录、表单等） | ✅ | 已验证兼容多种平台 |
| 简单的页面抓取 | ❌ | 优先使用 browser skill |
| 需要多标签页并行 | ⚠️ | 支持但需手动管理 |

**触发关键词：**
- 浏览器操作："打开浏览器"、"用浏览器访问"
- 复杂页面："登录页面"、"表单填写"、"需要点击的页面"
- 协议拦截："阻止弹窗"、"拦截 App 唤起"
- 渲染问题："页面显示异常"、"需要真实浏览器"

### 前置要求

```bash
# Ubuntu/Debian
apt-get update
apt-get install -y xvfb google-chrome-stable python3-pip
pip3 install websocket-client
```

---

## 核心概念

### 路径定位

```
当前文件路径 = 本 SKILL.md 文件的路径
Skill 根目录 = 当前文件路径的父目录
脚本目录 = Skill 根目录 + /scripts/
场景目录 = Skill 根目录 + /scenarios/
```

**示例：**
- 当前文件: `~/.openclaw/workspace/skills/headed-browser-open-v3/SKILL.md`
- Skill 根目录: `~/.openclaw/workspace/skills/headed-browser-open-v3/`
- 脚本目录: `~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/`
- 场景目录: `~/.openclaw/workspace/skills/headed-browser-open-v3/scenarios/`

### 场景文件机制

**【强制】每次操作前必须读取场景文件：**

1. 确定 Skill 根目录
2. 提取目标域名
3. 构建场景文件路径：`{SKILL_ROOT}/scenarios/{domain}.md`
4. 读取场景文件（存在则读取，不存在则读取 `scenarios/generic.md`）

**场景文件索引：**

| 文件 | 何时加载 | 说明 |
|------|---------|------|
| `scenarios/platform-type-a.md` | 类型A网站 | 标准登录流程、DOM渲染 |
| `scenarios/platform-type-b.md` | 类型B网站 | Canvas渲染处理 |
| `scenarios/platform-type-c.md` | 类型C网站 | 复杂交互、建议使用JS点击 |
| `scenarios/generic.md` | 通用参考 | 通用原则和最佳实践 |

> 支持多网站场景，根据访问的域名自动匹配对应的场景配置。

---

## 工具脚本

### browser.sh - 浏览器管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `start [URL]` | 启动浏览器，可选打开URL | `browser.sh start "https://example.com"` |
| `status` | 检查运行状态 | `browser.sh status` |
| `stop` | 停止浏览器 | `browser.sh stop` |

**环境变量：**
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CDP_PORT` | 18800 | CDP 调试端口 |
| `DISPLAY_NUM` | 99 | Xvfb 显示号 |
| `SCREEN_WIDTH` | 1920 | 屏幕宽度 |
| `SCREEN_HEIGHT` | 1080 | 屏幕高度 |

### element.py - 元素操作

| 参数 | 说明 | 示例 |
|------|------|------|
| `--list-tabs` | 列出所有标签页 | `--list-tabs` |
| `--find-tab URL` | 根据URL查找标签页 | `--find-tab "example.com"` |
| `--find TEXT` | 查找包含指定文本的元素 | `--find "登录,手机号"` |
| `--click X Y` | 点击指定坐标 | `--click 1077 586` |
| `--click-text TEXT` | 点击包含指定文本的元素 | `--click-text "获取验证码"` |
| `--js-click` | 使用JavaScript点击（更可靠） | `--click-text "登录" --js-click` |
| `--type TEXT` | 在当前焦点元素输入文本 | `--type "13800138000"` |
| `--screenshot PATH` | 截图保存 | `--screenshot /tmp/page.png` |
| `--snapshot` | 打印 Playwright 风格页面快照 | `--snapshot` |
| `--full-content` | 打印完整内容（主页面+所有iframe） | `--full-content` |

**点击失败处理：**
1. 告知用户"点击失败，尝试使用JavaScript点击..."
2. 使用 `--js-click` 参数重试
3. 如仍失败，截图反馈当前状态

### element_iframe.py - iframe 处理

| 参数 | 说明 | 示例 |
|------|------|------|
| `--list-frames` | 列出所有 frames | `element_iframe.py --list-frames` |
| `--iframe PATTERN` | 指定 iframe (URL/name匹配) | `--iframe "x-URS"` |
| `--find-elements` | 查找 iframe 内元素 | `--iframe "163" --find-elements` |
| `--click-text TEXT` | 点击 iframe 内元素 | `--iframe "dl.reg" --click-text "登录"` |
| `--type TEXT` | 在 iframe 输入框输入 | `--iframe "x-URS" --type "email@163.com"` |

**Playwright 风格对比：**

| Playwright API | element_iframe.py 等效 |
|---------------|----------------------|
| `page.frames` | `--list-frames` |
| `page.frame_locator('iframe')` | `--iframe "pattern"` |
| `frame.locator('input').click()` | `--click-text "placeholder"` |
| `frame.fill('input', 'text')` | `--type "text"` |

---

## 操作流程

### 标准流程：打开网页并截图

**【重要】打开网页前先检查现有标签页：**

```bash
# 1. 检查是否已有匹配的标签页
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --list-tabs
# 或使用 --find-tab 查找特定页面
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --find-tab "example.com"

# 2. 如果已有匹配标签页，直接操作现有页面
# 如果没有，再启动新浏览器
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://example.com/login" &

# 3. 等待页面加载
sleep 3

# 4. 截图确认
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/page.png
```

### 标准流程：查找并点击元素

```bash
# 1. 查找页面元素
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --find "登录,手机号"

# 2. 点击元素（坐标或文本）
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click 1077 586
# 或
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click-text "获取验证码" --js-click

# 3. 截图确认
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/after_click.png
```

### 标准流程：输入文本

```bash
# 1. 点击输入框获取焦点
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click 960 438

# 2. 输入文本
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --type "13800138000"

# 3. 截图确认
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/after_type.png
```

---

## 重要提示

### 手机号登录流程（通用）

**必须先勾选"我已阅读并同意"，再点击"获取验证码"！**

| 顺序 | 操作 | 说明 |
|------|------|------|
| 1 | 输入手机号 | 在手机号输入框输入 |
| 2 | **勾选同意协议** | ⚠️ 必须先勾选 |
| 3 | 点击获取验证码 | 此时按钮才可点击 |

### 坐标定位技巧

**获取坐标的方法：**
1. 先截图查看当前页面状态
2. 使用图像编辑工具测量目标位置
3. 或使用 `--find` 查看元素大致位置

**常用分辨率坐标参考：**

| 分辨率 | 元素类型 | 1920x1080 | 1366x768 |
|--------|----------|-----------|----------|
| 高分辨率 | 复选框区域 | (1077, 586) | (768, 420) |
| 高分辨率 | 按钮区域 | (1256, 438) | (896, 315) |

### 强制截图要求

**每次操作后必须截图确认**

```bash
# 操作前截图
element.py --screenshot /tmp/before.png

# 执行操作
element.py --click 100 200

# 操作后截图
element.py --screenshot /tmp/after.png
```

### 二维码刷新注意事项

**当用户要求"刷新二维码"时，注意区分以下情况：**

| 情况 | 判断方法 | 操作方式 |
|------|---------|---------|
| 页面整体刷新 | 整个页面重新加载，URL 不变 | 使用 `browser.sh start <URL>` 重新打开 |
| 点击刷新按钮 | 二维码区域有刷新/换一张按钮 | 使用 `element.py --click-text "刷新"` 或 `--click` 点击按钮 |
| 二维码自动过期 | 页面提示二维码已过期 | 先截图确认，再点击刷新按钮 |

**常见误区：**
- ❌ 直接刷新整个页面（会丢失已填写的表单数据）
- ✅ 先截图确认页面状态，找到刷新按钮并点击

**建议操作流程：**
```bash
# 1. 先截图查看当前状态
element.py --screenshot /tmp/qr_status.png

# 2. 查找刷新按钮
element.py --find "刷新,换一张,重新加载"

# 3. 点击刷新按钮（而非刷新整个页面）
element.py --click-text "刷新"

# 4. 确认新二维码已生成
element.py --screenshot /tmp/qr_new.png
```

---

## 页面内容识别

### 为什么需要同时获取主页面和 iframe 内容？

现代网站广泛使用 iframe 来隔离内容（如登录框、支付表单、第三方嵌入）。仅查看主页面内容会遗漏关键信息：

| 场景 | 主页面可见 | iframe 内容 | 示例 |
|------|-----------|-------------|------|
| 163 邮箱登录 | 空白或提示 | 完整的登录表单 | 登录 iframe |
| 小红书授权 | 授权按钮 | 授权详情和确认 | 第三方登录 |
| 支付页面 | 订单信息 | 支付密码输入 | 支付 iframe |

### 获取完整页面内容

使用 `--full-content` 参数同时获取主页面和所有 iframe 的内容：

```bash
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --full-content
```

**输出示例：**

```
======================================================================
📄 完整页面内容分析
======================================================================

🌐 主页面: 示例网站
   URL: https://example.com

   🌳 无障碍树: 15 个元素
      [1] [heading] '欢迎登录'
      [2] [textbox] '请输入手机号'
      [3] [button] '获取验证码'

📦 发现 2 个 iframe:

   ┌─ iframe [1] login-frame
   │  URL: https://login.example.com/form
   │  标题: 安全登录
   │  内容: 请输入您的账号和密码...
   │  元素: 5 个
   │    [1] INPUT[text]: '邮箱/手机号'
   │    [2] INPUT[password]: '密码'
   │    [3] BUTTON: '登录'
   │    [4] A: '忘记密码'
   └─

   ┌─ iframe [2] captcha-frame
   │  URL: https://captcha.example.com/verify
   │  ⚠️  无法访问: 跨域限制
   └─

======================================================================
```

### 页面快照对比

| 参数 | 用途 | 适用场景 |
|------|------|---------|
| `--snapshot` | Playwright 风格快照（主页面无障碍树） | 快速查看主页面结构 |
| `--full-content` | 主页面 + 所有 iframe 完整内容 | 识别登录框、嵌套表单 |
| `--find TEXT` | 搜索特定元素 | 定位已知元素 |

### 推荐识别流程

```bash
# 1. 首先获取完整页面内容（主页面 + iframe）
element.py --full-content

# 2. 根据识别结果，如有 iframe 需要操作
element_iframe.py --list-frames
element_iframe.py --iframe "login" --find-elements

# 3. 执行操作
element_iframe.py --iframe "login" --click-text "登录"

# 4. 截图确认
element.py --screenshot /tmp/result.png
```

### 邮箱登录示例（含 iframe）

```bash
# 1. 打开登录页面
browser.sh start "https://example.com/mail" &
sleep 3

# 2. 获取完整内容（发现登录在 iframe 中）
element.py --full-content
# 输出显示：
# 📦 发现 3 个 iframe:
#    ┌─ iframe [3] login-frame...
#    │  URL: https://login.example.com/...
#    │  元素: INPUT[text]: '邮箱/手机号'
#    │         INPUT[password]: '密码'
#    │         BUTTON: '登录'

# 3. 在 iframe 中输入账号
element_iframe.py --iframe "login" --type "your_email@example.com"

# 4. 点击登录
element_iframe.py --iframe "login" --click-text "登录"
```

---

## 技术原理

### 协议拦截实现

通过 Chrome 启动参数 `--inject-js` 在页面加载前注入 `blocker.js`：

```javascript
// 劫持 window.location
Object.defineProperty(window, 'location', {
    set: function(url) {
        if (url && !url.match(/^https?:\/\//i)) {
            console.log('[Blocker] Blocked:', url);
            return; // 阻止非 HTTP 协议
        }
        window.location.href = url;
    }
});
```

**拦截范围：**
- `window.location` setter
- `window.open()`
- `<a>` 标签点击事件

### 截图机制

```
--screenshot 执行流程：
1. 尝试 CDP 截图 (Page.captureScreenshot)
2. 成功 → 保存退出
3. 失败 → 回退到 Xvfb 截图 (import -window root)
4. 都失败 → 报错退出
```

### CDP 连接

```
element.py → WebSocket → Chrome CDP (port 18800)
                ↓
         执行浏览器操作
```

### iframe 处理原理

**Frame 树获取：**
```
CDP Page.getFrameTree
    ↓
返回: { frame, childFrames: [ { frame, childFrames... } ] }
    ↓
递归遍历得到所有 frames
```

**163 邮箱 iframe 结构示例：**
```
https://mail.163.com/ (主页面)
├── iframe: frameforlogin (about:blank)
├── iframe: frameJS6 (preload6.htm)
└── iframe: x-URS-iframe... (dl.reg.163.com) ← 登录表单
    ├── input: 邮箱/手机号
    ├── input: 密码
    ├── input: 验证码
    └── checkbox: 十天内免登录
```

---

## 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 浏览器启动失败 | Xvfb 未安装 | `apt-get install xvfb` |
| CDP 连接失败 | 浏览器未启动或端口冲突 | 检查 `browser.sh status`，更换 `CDP_PORT` |
| 元素找不到 | 页面未加载完成 | 增加 `sleep` 等待时间 |
| 点击无反应 | 坐标不正确 | 先截图确认元素位置，调整坐标 |
| 输入文本失败 | 输入框未获得焦点 | 先点击输入框再输入 |
| 截图失败 | CDP 和 Xvfb 都不可用 | 检查 `DISPLAY` 环境变量 |
| Chrome CPU 占用高 | 页面卡死或内存泄漏 | `pkill -9 chrome` 强制终止 |

### 强制终止 Chrome

```bash
# 强制终止所有 Chrome 进程
pkill -9 chrome

# 同时终止 Xvfb
pkill -9 Xvfb

# 检查残留进程
ps aux | grep -E "chrome|Xvfb" | grep -v grep
```

### 空闲自动回收

**默认行为：** 浏览器启动后，如果 **1 小时内没有任何操作**，会自动停止浏览器和 Xvfb 以释放资源。

**触发操作（会重置计时器）：**
- 任何 `element.py` 操作（点击、输入、截图等）
- 列出标签页 (`--list-tabs`)
- 查找元素 (`--find`)

**手动控制空闲超时：**
```bash
# 设置 30 分钟超时（默认 1 小时）
export IDLE_TIMEOUT=1800
browser.sh start

# 禁用自动回收（不推荐）
export IDLE_TIMEOUT=0
```

**监控日志：**
```bash
# 查看空闲监控日志
tail -f /tmp/idle-monitor.log
```

---

## 最佳实践

### 1. 操作前规划
- 明确目标：需要打开什么页面？执行什么操作？
- 检查是否有对应场景文件
- 预估操作步骤和等待时间

### 2. 稳健的操作节奏
```bash
# 好：每步操作后等待并截图
browser.sh start URL
sleep 3
element.py --screenshot step1.png
element.py --click 100 200
sleep 1
element.py --screenshot step2.png

# 不好：连续操作不等待
browser.sh start URL
element.py --click 100 200
element.py --type "text"  # 可能页面还没加载完
```

### 3. 错误处理
- 操作失败后先截图查看当前状态
- 检查浏览器是否仍在运行
- 必要时重启浏览器

### 4. 资源清理
- 任务完成后执行 `browser.sh stop` 清理资源
- 长时间运行的任务定期检查 Chrome 进程状态

### 5. 经验记录
**操作中发现新问题 → 立即更新场景文件：**
- 失败经验 → 添加到"已知陷阱"章节
- 成功经验 → 添加到"有效模式"章节
- 坐标/参数调整 → 更新对应表格

---

## 文件结构

```
headed-browser-open-v3/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── browser.sh                    # 浏览器启动/停止脚本
│   ├── element.py                    # 元素操作脚本
│   ├── element_iframe.py             # iframe 处理脚本
│   ├── idle-monitor.sh               # 空闲监控和资源回收
│   ├── blocker.js                    # 协议拦截 JavaScript
│   └── playwright_iframe_demo.py     # Playwright iframe 示例
└── scenarios/
    ├── platform-type-a.md            # 类型A网站场景
    ├── platform-type-b.md            # 类型B网站场景
    ├── platform-type-c.md            # 类型C网站场景
    └── generic.md                    # 通用场景
```

---

## 附录

### Playwright iframe 处理

**脚本位置：** `scripts/playwright_iframe_demo.py`

**运行示例：**
```bash
# 安装依赖
pip3 install playwright
playwright install chromium

# 运行示例
cd ~/.openclaw/workspace/skills/headed-browser-open-v3
python3 scripts/playwright_iframe_demo.py
```

**API 对比：**

| 功能 | CDP (本 skill) | Playwright |
|------|---------------|------------|
| 获取 frame 树 | `Page.getFrameTree` | `page.main_frame` + `frame.child_frames` |
| 进入 iframe | 手动切换 context | `page.frame_locator(selector)` |
| 操作 iframe 元素 | `Runtime.evaluate` | `frame_locator.locator().click()` |
| 跨域处理 | 需创建独立 session | 自动处理 |

### 版本对比

| 特性 | V2 | V3 |
|------|-----|-----|
| 核心功能 | ✅ | ✅ |
| 代码复杂度 | 较高 | **简化** |
| 场景文件 | 强制使用 | 参考使用 |
| 架构 | 复杂 | **精简** |
| 维护性 | 一般 | **更好** |

### 相关链接

- [Playwright 官方文档](https://playwright.dev/python/docs/api/class-framelocator)
