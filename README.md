# 🌌 AntGravity MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Supported-orange.svg)](https://modelcontextprotocol.io/)

> **AntGravity MCP Server** 是一款运行在 Windows 物理宿主机上的高强度 Agentic 协作层服务器。它基于标准 **Model Context Protocol (MCP)** 协议，利用 FastAPI 与 Streamable HTTP SSE 传输通道，实现跨主机的智能体调用。
>
> 远程容器客户端（如 **Hermes Agent**）可以通过本项目暴露的 **27 个系统级专属工具**，顺畅地驱动 Windows 环境，完成 PowerShell 指令下发、Playwright 浏览器自动化、Git 流水线协同、Android APK 自动编译以及共享黑板看板管理。

---

## 📐 架构设计

```text
       +---------------------------------------------+
       |             Hermes Agent (容器内)           |
       |                  [MCP Client]               |
       +----------------------+----------------------+
                              |
                              | MCP over SSE (HTTP:9000/mcp)
                              v
       +---------------------------------------------+
       |         AntGravity MCP Server (Windows)     |
       |                  [MCP Server]               |
       +-----+----------------+----------------+-----+
             |                |                |
             v                v                v
     [Windows 命令行]   [Playwright 浏览器]  [共享黑板看板]
    PowerShell & Cmd    Chrome/Edge/WebView2    SQLite Kanban
             |                |                |
             v                v                v
     (Android 构建等)   (网页自动化/截图)    (Agent 状态同步)
```

---

## 🛠️ 27 个注册工具全景

本项目不仅仅是简单的文件管理，而是深度为 **智能体开发与状态同步** 打造的协作中心。已实现并成功通过端到端测试验证的工具列表如下：

### 1. 系统与命令行 (System & Command)
| 工具名称 | 功能描述 | 关键参数 |
| :--- | :--- | :--- |
| `ag_health_check` | 检查 Windows 系统健康度，报告 Java、Git 及 Android SDK 环境 | — |
| `ag_powershell` | 执行安全的 PowerShell 命令，并实时捕获进程的 Stdout/Stderr | `command`, `timeout` |

### 2. 文件系统管理 (Secure Filesystem)
| 工具名称 | 功能描述 | 关键参数 |
| :--- | :--- | :--- |
| `ag_file_list` | 限制安全目录（如 `D:\Obsidian\sync\task`）的文件遍历与通配符筛选 | `path`, `pattern` |
| `ag_file_read` | 安全读取工作区的文件内容，并支持编码自动防错处理 | `path`, `encoding` |
| `ag_file_write` | 安全写入并自动创建多级父目录 | `path`, `content` |
| `ag_file_exists` | 快速判断指定路径是否存在 | `path` |

### 3. Playwright 浏览器自动化 (Headless Browser)
| 工具名称 | 功能描述 | 关键参数 |
| :--- | :--- | :--- |
| `ag_browser_open` | 懒加载启动本地 Chrome/Edge 实例并导航至 URL | `url`, `wait_until` |
| `ag_browser_screenshot` | 对已打开的网页执行完整截图，返回 Base64 或保存到本地 | `page_id`, `full_page` |
| `ag_browser_click` | 通过 CSS 选择器进行高精度的点击交互 | `page_id`, `selector` |
| `ag_browser_fill` | 输入表单或搜索框内容 | `page_id`, `selector`, `value` |
| `ag_browser_get_text` | 获取页面正文，自动移除脚本与样式标签 | `page_id` |
| `ag_browser_get_html` | 获取指定 DOM 节点的原始 HTML 结构 | `page_id`, `selector` |
| `ag_browser_eval` | 执行任意 JavaScript 表达式，返回可序列化的计算结果 | `page_id`, `expression` |
| `ag_browser_wait` | 动态等待页面元素的状态变更 | `page_id`, `selector`, `state` |
| `ag_browser_list_pages` | 检索当前 MCP 服务管理的所有打开的页面 ID | — |
| `ag_browser_close` | 关闭指定页面或销毁整个浏览器实例 | `page_id` |

### 4. Git 协同流水线 (Git Pipeline)
| 工具名称 | 功能描述 | 关键参数 |
| :--- | :--- | :--- |
| `ag_git_clone` | 远程代码克隆，支持特定分支与深度拉取 | `repo_url`, `target_dir` |
| `ag_git_status` | 检查工作区代码变动与提交进度 | `repo_dir` |
| `ag_git_apply_patch` | 极速应用变更补丁，实现零冲突的自动化热更新 | `repo_dir`, `patch_text` |
| `ag_git_commit` | 一键打包提交修改，支持规范化的提交日志 | `repo_dir`, `message` |

### 5. 构建与测试集成 (Automated Build)
| 工具名称 | 功能描述 | 关键参数 |
| :--- | :--- | :--- |
| `ag_run_gradle` | 驱动 Gradle 编译，捕获尾部构建日志 | `project_dir`, `task` |
| `ag_run_npm` | 执行 Node 项目依赖安装与前端工程打包任务 | `project_dir`, `script` |
| `ag_run_python` | 执行特定的测试或数据处理脚本 | `project_dir`, `args` |

### 6. Android 工具链与编译 (Android SDK Suite)
| 工具名称 | 功能描述 | 关键参数 |
| :--- | :--- | :--- |
| `ag_android_check_env` | 校验本地 Android SDK、NDK、CMake 工具链的完整度 | — |
| `ag_android_install_cmdline_tools` | 自动下载并设置 Android 命令行打包核心套件 | — |
| `ag_android_install_sdk` | 自动下载并许可特定的 SDK、NDK 构建平台和 CMake 版本 | `packages` |
| `ag_android_build_apk` | 执行打包，自动输出 Release / Debug 的正式 APK 文件 | `project_dir`, `variant` |
| `ag_android_find_apks` | 检索编译成功的 APK 包文件，便于打包输出或上传 | `project_dir` |

### 7. AntGravity 浏览器 CDP 桥接 (Tauri & CDP Bridge)
| 工具名称 | 功能描述 | 关键参数 |
| :--- | :--- | :--- |
| `ag_cdp_status` | 监测本地 AntGravity 实例的调试端口 (:9000) 可达性 | — |
| `ag_cdp_list_pages` | 罗列 AntGravity 所有的 Tauri 页面视图 | — |
| `ag_cdp_eval` | 通过 Web 调试协议动态向客户端 UI 注入执行逻辑 | `page_id`, `expression` |
| `ag_launch_antgravity_cdp` | 自启动带远程调试端口的客户端实例 | — |

### 8. 实时状态流与共享黑板 (Kanban & Real-time Stream)
| 工具名称 | 功能描述 | 关键参数 |
| :--- | :--- | :--- |
| `ag_record_step` | 记录推理与行为日志至工作区 `.hermes-stream/` 方便随时回溯 | `type`, `content`, `meta` |
| `ag_get_current_status` | 非阻塞获取当前 Agent 的执行卡点或等待授权状态 | `workdir` |
| `ag_get_step_history` | 回溯过去执行的链条，确保追赶及归档顺畅 | `workdir`, `limit` |
| `ag_accept_action` | 向动作确认队列下发外部指令（如同意执行高危命令） | `workdir`, `action`, `step_id` |
| `ag_kanban_create` | 在共享 SQLite 黑板中创建看板任务卡片 | `title`, `body`, `assignee` |
| `ag_kanban_update` | 更新看板任务卡片的状态或成果链接 | `task_id`, `status`, `result` |
| `ag_kanban_comment` | 为指定任务追加跨智能体协同评论 | `task_id`, `body`, `author` |
| `ag_kanban_complete` | 完成看板任务，记录总计耗时与元数据快照 | `task_id`, `summary` |
| `ag_kanban_list` | 过滤并获取当前名下的所有黑板待办卡片 | `assignee`, `status` |
| `ag_kanban_get` | 精确查询单张任务卡片的详细历史记录与父子依赖 | `task_id` |

---

## ⚡ 快速开始

### 1. 克隆与依赖安装

在 Windows PowerShell 下执行：

```powershell
# 克隆仓库
git clone https://github.com/Gmatrix2022/antgravity-mcp-server.git
cd antgravity-mcp-server

# 安装依赖
pip install -r requirements.txt

# 初始化 Playwright 浏览器依赖 (内置 msedge 支持)
playwright install msedge
```

### 2. 本地服务启动

您可以直接通过 Python 启动轻量化服务：

```powershell
python server.py
```
* 服务将在本地的 `http://localhost:9000` 监听。
* SSE 工具发现接口位于 `http://localhost:9000/mcp`。

若需长效后台运行，可注册为 Windows 系统服务：
```powershell
# 详细步骤见脚本及 D:\Obsidian\sync\task\antgravity-mcp-server\STATUS.md
```

### 3. 配置局域网安全访问

为了允许容器客户端（如处于其他 IP 的 Hermes 容器）远程连接 Windows 宿主机的 `9000` 端口，需在 Windows 侧添加一条防火墙入站许可：

```powershell
New-NetFirewallRule -DisplayName "AntGravity MCP Server 9000" -Direction Inbound -Protocol TCP -LocalPort 9000 -Action Allow
```

---

## 🔒 安全性控制与约束

> [!IMPORTANT]
> 由于 MCP 赋予了外部智能体在 Windows 主机执行系统级和 PowerShell 操作的能力，本项目从架构层面设计了极致的安全防护防线：

1. **工作区隔离**：所有文件读写类工具（`ag_file_*`）严格限制其在白名单工作区内（如 `D:\Obsidian\sync\task\`、`D:\dev\`、`D:\AndroidProjects\`），任何穿梭至高危系统盘（如 `C:\Windows\` 或 `C:\Users\keche\.ssh\`）的路径请求都将被底层拦截并返回 403。
2. **PowerShell 严格黑名单**：高危命令（如 `Remove-Item -Recurse C:\`、`Format-Volume`、`Stop-Computer`、`reg delete`、修改用户组等）均内置正则拦截审查机制，从根源规避意外损毁系统。
3. **敏感文件屏蔽**：即使在工作区内，`.env`、SSH 密钥等敏感隐私配置文件也是文件读取工具的永久违禁品。
4. **日志安全审查**：所有工具调用时间、来源、入参及 exit_code 将会被全程加密落盘记录于工作区 `logs/server.log`，方便人工随时排查与复盘审计。

---

## 🧪 自动化测试验证

项目内置了完整的 E2E (端到端) 测试套件，用于确认 27 个工具协议的兼容性。

确保服务在 `9000` 端口运行后，执行本地测试脚本：

```powershell
python test_mcp.py
```

若输出 `[1/8]... [8/8] 测试完成!` 且无报错，则说明 MCP 工具引擎已完美就绪。

---

## 📄 开源许可证

本项目基于 **MIT** 许可证进行分发与二次开发，详情请参阅 `LICENSE`。
