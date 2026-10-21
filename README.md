# 销售对练实验室 · Sales Practice Lab

面向求职展示的销售沟通训练 Demo：在同一界面体验 **TOB 门店合作**与 **TOC 消费者咨询**，完成场景选择、角色对话、证据复盘和记录导出。

所有机构、人物、产品、价格及场景均为本 Demo 新编的虚构资料。公开工程没有复制历史项目的原始业务库、合同、录音、商业政策、凭证或编译模块。

## 在线体验

**[打开公开演示网站](https://lazydell-sales-roleplay.bravedaisy258.chatgpt.site)** — 无需登录、安装或模型密钥。

在线版在浏览器内运行规则模拟，支持 TOB/TOC、角色互换、证据复盘和导出。对话不发送到应用服务器，刷新后清空。真实模型功能需下载下方 Python 本地版配置使用。在线版与本地版采用不同的种子洗牌实现，不保证两者追问顺序一致。

## 项目亮点

| 设计问题 | 实现方式 |
| --- | --- |
| 企业合作与个人销售目标不同 | 场景、角色、复盘维度分开维护，界面统一 |
| 面试演示不应依赖密钥 | 默认规则模拟，可选服务端模型接口 |
| 角色切换容易污染上下文 | 新建隔离会话，固定当前产品快照 |
| 评分容易缺少依据 | 引用用户原话，提供明确标注的关键词覆盖提示 |
| 业务资料不能直接公开 | 独立合成数据、文件扫描和发布包允许列表 |

项目介绍详见 [项目说明书](docs/project-overview.md)，三分钟演示可参考 [演示脚本](docs/demo-script.md)。

## 30 秒启动

需要 Python 3.12 或更高版本，不需要 pip、Node.js、数据库或模型密钥。

```sh
git clone https://github.com/LazyDell/sales-roleplay-demo.git
cd sales-roleplay-demo
python3 start.py
```

Windows 可用 `py -3.12 start.py`。打开 http://127.0.0.1:8765 。端口占用时运行 `python3 start.py --port 8766`。终端按 Ctrl+C 停止。服务仅绑定本机回环地址。

## 体验路线

1. 选择 TOB「新店拜访」和一个虚构产品，点击开始。
2. 提问「您目前最担心哪个环节的工作量？」观察模拟回复。
3. 说明服务范围和限制，再提出试点或复盘安排。
4. 点击结束并复盘，查看各维度匹配到的用户原话，导出本轮 JSON。
5. 切换 TOC，或勾选角色互换后开始新一轮。

默认是**规则模拟**，不是模型推理。复盘是**关键词覆盖提示**，不是 AI 评分，也不衡量真实销售能力。反问、否定或无关表达可能触发匹配；页面保留证据供人工核对。角色互换时仅回顾对话，不评价客户角色的销售能力。

## 已实现

- 两种训练模式、四个虚构场景、两个独立产品事实卡。
- 常规/追问难度与可复现的模拟追问顺序。
- 新会话隔离角色与历史，最多 20 轮，2 小时有效。
- 模拟回复、可选服务端模型适配、失败后保留输入供重试。
- 不混用产品卡的上下文构建；真实模型仍可能产生错误，需对照事实卡审阅。
- 基于原话的规则复盘、客户端 JSON 下载。
- 响应式中文界面，无外部字体、统计脚本或 CDN。
- 自动化测试、公开文件扫描、发布包生成和 GitHub Actions 检查。

## 可选：真实模型

适配的接口合同为 `POST {MODEL_BASE_URL}/chat/completions`，请求包含 `model/messages/temperature`，响应读取 `choices[0].message.content`。仅支持兼容这一合同的服务，不代表已验证所有供应商。

在启动服务的终端设置 `MODEL_BASE_URL`、`MODEL_NAME`，需要鉴权时再设置 `MODEL_API_KEY`。示例使用本机兼容服务：

```sh
export MODEL_BASE_URL=http://127.0.0.1:11434/v1
export MODEL_NAME=your-local-model
python3 start.py
```

`.env.example` 仅说明变量名，程序不会自动加载 `.env`。配置后刷新页面，在引擎列表主动选择真实模型；默认仍是模拟模式。密钥不下发到浏览器、不写入记录。模型地址只允许 HTTPS 或本机 HTTP，禁止自动跟随重定向。真实模型会接收本轮输入，演示时请只输入虚构内容。

## 验证与打包

在项目根目录运行：

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_public.py
node --test tests/test_static.js
python3 tools/package_public.py ../sales-roleplay-demo-public.zip
```

扫描会阻止环境文件、未知文件类型、二进制、压缩包、符号链接，以及部分公司/个人信息和密钥模式。扫描器不等于语义保密审查；新增资料应保持虚构来源并人工审阅。打包只从本工程读取，输出不能位于工程内部；已有包不会覆盖。

**只将本目录作为 GitHub 仓库根目录，不要上传其父目录。** 独立 Git 仓库不包含原工程历史；发布前检查 `git status`、暂存差异和 `python3 tools/check_public.py --tracked`。只发布经扫描的源码和虚构演示资料。

## 结构

```text
frontend/       原生 HTML、CSS、JavaScript
backend/        标准库 HTTP 服务、会话、模型适配与规则复盘
scenarios/      分开的 TOB / TOC 虚构场景
prompts/        通用角色行为约束
data/           虚构产品事实卡
tests/          角色、产品、失败路径与 HTTP 边界测试
tools/          公开文件扫描及打包工具
docs/           设计说明、演示脚本与验收记录
```

## 构建静态在线版

```sh
python3 tools/build_static.py ../sales-roleplay-web
python3 -m http.server 8770 --directory ../sales-roleplay-web
```

在线版构建仅需 Python；测试浏览器规则引擎需要 Node.js 22+。构建产物为五个静态文件，可以托管到支持 HTTPS 的静态站点平台。当前正式网站托管在 Sites；GitHub 更新不会自动触发 Sites 发布，需要重新构建并发布。

## 已知边界

这是本机演示应用，不是可直接面向公网部署的多租户系统。未实现登录、持久化数据库、语音识别/合成、多人对练和模型自动评分。重启后会话消失；浏览器刷新后不会恢复当前会话。导出文件包含用户输入，分享前请检查。

真实模型提示词只是行为约束，不是严格的事实或注入防护保证。此版本尚未使用付费模型、Windows 实机或实际手机验收。公开托管前需要生产级服务、鉴权、配额和运维设计。

参见 [设计说明](docs/architecture.md)、[面试演示脚本](docs/demo-script.md)、[验收记录](docs/validation.md)。尚未指定开源许可证；发布前由项目所有者决定授权范围。
