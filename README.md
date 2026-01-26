# 互动大屏幕系统 (Interactive Display System)

## 项目说明

本项目是为了企业内部培训开发的一个可部署在局域网内的互动网站系统。该系统设计用于投屏到会议室大屏幕，供参会人员查看，页面风格适配大屏幕显示（接近 PPT 风格）。

系统包含三个主要视图：
*   **公共页面**：适配 PC 屏幕/大屏，用于展示互动内容、实时结果和统计数据。
*   **配置页面**：适配 PC 屏幕，供管理员配置培训主题和互动内容（需密码访问）。
*   **用户页面**：适配手机屏幕，参会人通过扫描二维码签到后进入，进行答题、投票等互动操作。

## 快速开始 (Quick Start)

### 环境要求
*   Python 3.9+

### 安装与启动
本项目提供了一个启动脚本 `run.py`，它会自动检测并安装所需的依赖包 (`requirements.txt`)。

在项目根目录下运行：

```bash
python run.py
```

如果需要手动安装依赖：
```bash
pip install -r requirements.txt
python run.py
```

### 访问地址
服务启动后（默认端口 8000），可以通过以下地址访问：

*   **大屏幕入口 (Display)**: [http://localhost:8000/](http://localhost:8000/)
*   **管理员入口 (Admin)**: [http://localhost:8000/admin](http://localhost:8000/admin)
*   **手机签到 (Mobile)**: [http://localhost:8000/signin](http://localhost:8000/signin)

## 功能特性

### 1. 签到系统
*   **扫码签到**：首页显示动态二维码，用户手机扫号码签到。
*   **实时统计**：大屏幕实时显示已签到人数。
*   **身份识别**：支持普通参会人和主持人身份（主持人需密码认证）。
*   **防重复**：自动识别已签到用户。

### 2. 互动插件 (Plugins)
系统采用插件化设计，支持多种互动形式。目前包含：
*   **ai_survey**: 问卷与答题互动。
*   **demo_vote**: 投票互动演示。
*   **demo_finder**: 寻找数字游戏演示。

### 3. 后台管理
*   **培训配置**：设置培训主题、重置培训记录、导出数据。
*   **互动控制**：主持人/管理员可配置互动内容的显示时间、类型，并实时控制互动的开启与结束。

## 技术栈
*   **后端**: Python FastAPI, SQLAlchemy, Uvicorn, Websockets
*   **前端**: Jinja2 模板, 原生 JavaScript/CSS (无需前端构建工具)
*   **工具**: python-multipart, qrcode, aiofiles

## 目录结构
*   `app/`: 核心应用代码 (路由, 数据库模型, 静态资源)
*   `plugins/`: 互动插件目录
*   `run.py`: 项目启动脚本
*   `requirements.txt`: Python 依赖列表