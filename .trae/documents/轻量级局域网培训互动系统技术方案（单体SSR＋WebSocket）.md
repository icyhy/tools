## 目标与约束
- 轻量级、单体应用、SSR 模式，不前后端分离。
- 一键运行、跨平台（macOS/Windows/Linux）。
- 技术栈：Python 3.11+、FastAPI（含 Starlette WebSocket）、Jinja2、SQLite。
- 符合 docs/README.md 与 REQUIREMENTS.md 的业务要求，支持插件化互动、管理员配置、主持人/参会人互动、200 人并发。
- 明确约束：活动二维码不包含角色参数；主持人密码在后台启动培训时设置（默认 admin123）；统计图表样式以适合大屏展示为准。

## 总体架构
- **单体服务**：FastAPI + Uvicorn，统一提供页面（Jinja2 SSR）与数据接口。
- **实时通道**：WebSocket 广播会议与插件状态（大屏/主持人/参会人三端同步）。
- **模板渲染**：Jinja2 模板分别适配大屏（PPT风）、PC配置页、手机端页。
- **插件机制**：后端 Python 插件 + 前端模板/静态资源；目录扫描、热加载、统一事件通道。
- **数据层**：SQLite（内置，便于解压即用）；必要时支持切换至 Postgres。

## 页面与路由
- 大屏首页（二维码/人数/Logo/指引）：GET `/`，SSR 模板 `display/index.html`。
- 手机签到页：GET `/signin`（二维码链接指向该页），POST `/api/signin`。
- 主持人控制页：GET `/host`，POST `/api/host/login`（密码校验），操作插件与流程。
- 管理员配置页：GET `/admin`，POST `/api/admin/start`（设置主持人密码，默认 admin123），插件选型与参数配置、重置、导出。
- 插件公共页：GET `/display/{plugin_id}`，用户页：GET `/user/{plugin_id}`，主持人页：GET `/host/{plugin_id}`。
- WebSocket：`/ws/event/{event_id}`（含房间/角色会话），统一事件：`GameStart`、`GameEnd`、`UpdateScore` 等。
- 导出：GET `/api/admin/export`（CSV/XLSX）。

## 身份与二维码策略
- 二维码仅包含活动入口（含活动ID/短码），不带角色参数。
- 手机进入后在页面选择身份：参会人或主持人；主持人需输入后台设置的密码。
- 会话：基于签入生成的临时会话ID（cookie + server-side），同浏览器自动识别老用户。

## 数据模型（示意）
- events(id, title, started_at, host_password_hash)
- participants(id, event_id, name, dept, role[host/user], code4)
- plugins(id, name, enabled, config_json)
- plugin_instances(id, event_id, plugin_id, status, state_json)
- plugin_logs(id, instance_id, user_id, action, payload_json, ts)
- results(id, instance_id, type, data_json)

## 插件规范与生命周期
- 目录结构：`plugins/<plugin_key>/`
  - `plugin.py`：实现 `BasePlugin`（id/name/schema/start/stop/handle_input/broadcast）。
  - `templates/`：`display.html`、`user.html`、`host.html`（Jinja2）。
  - `static/`：该插件的静态JS/CSS（尽量原生JS，少依赖）。
  - `manifest.json`：元数据与可配置项（时长、题库等）。
- 热加载：后台刷新时扫描目录，使用 `importlib` 加载/重载；配置页可勾选启用插件并填入参数。
- 状态同步：插件通过统一事件总线广播；服务端维护实例状态，持久化需要的数据。

## MVP 内置互动
1. 找数字规律（含三轮不同布局/排序规则；倒计时与统计）。
2. 现场问答（题库来源 Markdown；手机端选项，统计正确率）。
3. 投票/表决（动态选项；大屏统计图表）。

## 大屏展示与图表
- 主题：高对比、大字号、简洁动画；适应会议室投屏。
- 图表库：Chart.js（前端直接用，免打包），或纯 SVG 渲染（更轻）。
- 样式：提供默认主题与少量配色变量；可在插件层覆盖。

## 安全与性能
- 密码：管理员设置主持人密码，默认 admin123；后端只存 hash（如 bcrypt）。
- 基础防护：输入校验、XSS 过滤、CSRF（针对表单 POST），WebSocket 鉴权（活动ID+会话令牌）。
- 并发：异步IO，事件房间广播；对热点操作限速；200人并发目标。

## 部署与一键运行
- 依赖：Python 3.11+；建议使用 `uv`（或 `pipx`）快速安装依赖。
- 一键运行：`python -m app` 或 `uv run app:main` 自动启动 Uvicorn 并打开本机地址。
- 配置：首启引导页设置培训主题与主持人密码；静态资源与模板随应用打包。
- 可选：Docker 单容器（非必须）。

## 与现有文档的对应更新
- 更新 REQUIREMENTS.md 的“互动插件结构”小节，补充插件目录/接口/模板规范与热加载策略。
- 明确二维码与身份策略、主持人密码的配置点与默认值。
- 补充路由列表、数据模型、事件总线与并发目标说明。

## 待确认点（含默认处理）
- 题库 Markdown 的具体格式（默认约定：题目、选项、答案三段结构）。
- 导出文件格式（默认 CSV + XLSX）。
- 活动单场数据清理策略（默认后台“重置”会清空当前场次相关记录）。
- 图表主题是否需公司品牌色（默认提供通用主题并支持后台配置主色）。

## 里程碑
- M1：框架与页面骨架、二维码签到、基础会话、管理员配置。
- M2：WebSocket 通道、插件系统与热加载、投票插件。
- M3：问答与找规律插件、统计图表、导出功能、样式打磨。