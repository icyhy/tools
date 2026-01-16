# 系统架构设计 (ARCHITECTURE.md)

## 1. 架构概览
本系统采用 **B/S 架构**，后端基于 ASP.NET Core 8.0，前端采用 **Vue.js 3**，通过 SignalR 进行实时双向通信。核心特色是**基于文件系统的插件化架构**，允许动态扩展互动内容。

### 1.1 系统拓扑图
```mermaid
graph TD
    User[参会人 (Mobile)] -->|HTTP/WebSocket| Server[ASP.NET Core Server]
    Host[主持人 (Mobile)] -->|HTTP/WebSocket| Server
    Screen[大屏 (PC Browser)] -->|HTTP/WebSocket| Server
    
    subgraph "Server Node (Local LAN)"
        Server -->|Read/Write| DB[(SQLite Database)]
        Server -->|Load| Plugins[Plugin Folder]
        Plugins -->|Contains| StaticFiles[HTML/JS/CSS]
        Plugins -->|Contains| Logic[Server Logic (Script/DLL)]
        Plugins -->|Contains| Config[Markdown Config]
    end
```

## 2. 后端设计 (Backend)

### 2.1 核心模块
1.  **Identity Service**: 
    *   管理用户会话 (Session)。
    *   生成/验证 4 位数随机 ID。
    *   角色鉴权 (Host vs Participant)。
2.  **Plugin Manager**:
    *   **Discovery**: 启动时/运行时扫描 `/Plugins` 目录。
    *   **Loader**: 解析 `config.md` 元数据，注册静态文件路由。
    *   **Lifecycle**: 管理插件的加载、卸载、更新。
3.  **Interaction Engine (SignalR Hub)**:
    *   `MainHub`: 处理全局消息（签到、系统状态）。
    *   `GameHub`: 处理具体互动逻辑（答题、游戏数据）。
    *   **状态机**: 维护当前互动环节的状态 (Idle -> Ready -> Running -> Finished)。
4.  **Data Repository**:
    *   使用 EF Core 操作 SQLite。
    *   表结构: `Users`, `Sessions`, `InteractionRecords`, `PluginConfigs`.

### 2.2 插件加载机制
每个插件被视为一个独立的静态资源包 + 配置。
*   **路由映射**: `/plugins/{pluginId}/*` -> 物理路径 `/Plugins/{pluginId}/*`。
*   **配置解析**: 解析 Markdown Front Matter 获取元数据 (Name, Icon, Type)。

## 3. 前端设计 (Frontend)

### 3.1 宿主应用 (Host App)
一个轻量级的 SPA (Single Page Application)，负责：
*   **全局状态管理**: WebSocket 连接状态、当前用户信息。
*   **路由分发**: 根据服务器指令，使用 **vue3-sfc-loader** 动态远程加载插件的 `.vue` 入口文件，挂载到当前视图中。
*   **公共组件**: 顶部状态栏、Toast 提示、Loading 动画。

### 3.2 插件前端规范
插件前端需暴露标准生命周期钩子 (Window 挂载对象)：
```javascript
window.InteractionPlugin = {
    init: (context) => { ... }, // 初始化，获取 socket 实例
    start: () => { ... },       // 游戏开始
    stop: () => { ... },        // 游戏结束
    onMessage: (msg) => { ... } // 接收服务端自定义消息
};
```

## 4. 数据库设计 (Schema)

### 4.1 Users 表
| Field | Type | Description |
| :--- | :--- | :--- |
| Id | GUID | 主键 |
| ShortId | string | 4位显示ID (唯一索引) |
| Name | string | 姓名 |
| Role | enum | User, Host, Admin |
| CreatedAt | datetime | 注册时间 |

### 4.2 InteractionLogs 表
| Field | Type | Description |
| :--- | :--- | :--- |
| Id | GUID | 主键 |
| PluginId | string | 关联的插件ID |
| UserId | GUID | 用户ID |
| Data | JSON | 提交的数据 (如答案、摇动次数) |
| Score | int | 得分 |
| Timestamp | datetime | 提交时间 |

## 5. 接口设计 (API)

### 5.1 HTTP API
*   `GET /api/auth/me`: 获取当前用户信息。
*   `POST /api/auth/login`: 用户注册/登录。
*   `GET /api/plugins`: 获取可用插件列表 (Admin only)。
*   `POST /api/interaction/start`: 启动指定互动 (Host only)。

### 5.2 SignalR Events
*   **Server -> Client**:
    *   `SystemStatus`: 全局状态变更 (跳转页面)。
    *   `PlayerCount`: 在线人数更新。
    *   `GameEvent`: 游戏内事件 (倒计时、排名更新)。
*   **Client -> Server**:
    *   `JoinGame`: 加入当前互动。
    *   `SubmitAction`: 提交互动数据 (需限流)。

## 6. 安全与性能
*   **并发控制**: SignalR 使用 Redis Backplane (可选，单机版暂不需要) 或内存队列处理高并发消息。
*   **防作弊**: 关键逻辑 (如计分、答案校验) 在服务端进行，前端仅负责展示。
*   **输入过滤**: 全局防止 XSS 和 SQL 注入。

## 7. 开发计划 (Future Steps)
1.  **脚手架搭建**: 
    *   Backend: ASP.NET Core Web API + SignalR + EF Core (SQLite).
    *   Frontend: Vue 3 + Vite + Tailwind CSS.
2.  **核心功能实现**:
    *   实现 SignalR Hub 和基础连接。
    *   实现插件扫描与 `.vue` 文件托管。
    *   集成 `vue3-sfc-loader` 到前端。
3.  **MVP 互动开发**:
    *   实现“找数字规律”插件。

