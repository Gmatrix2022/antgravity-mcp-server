# AntGravity MCP Server — STATUS

> 状态：**running** ✅ (已整合 `windows-mcp` 共 27 个工具，作为 Windows 系统服务持续运行在 9000 端口)  
> 更新时间：2026-05-20 22:54  

---

## 💻 当前配置

- **运行端口**：`9000`
- **本地访问**：`http://localhost:9000`
- **跨主机访问**：`http://192.168.0.124:9000`
- **服务托管**：Windows 系统服务 `AntGravityMCP`（NSSM 托管，使用本地用户 Python 环境运行，具有完整 win32 与 AppData 路径依赖）
- **防火墙**：规则 `AntGravity MCP 9000` 已启用（Inbound, Allow, TCP, Port 9000）
- **客户端连接**：来自远程 Ubuntu 主机 `192.168.0.126` 的 Hermes 容器的长连接已成功握手并保持 **Established** 状态。

---

## 📡 服务端点

| 路径 | 说明 |
| :--- | :--- |
| `/health` | 健康检查端点 (Phase 0) ── 绕过 DNS Rebinding，允许跨主机探测 |
| `/mcp` | FastMCP StreamableHTTP 端点 (Phase 1) ── 承载星闪 SSE 长连接与 27 个核心工具 |

---

## 🛠️ MCP 工具详情 (共 27 个工具)

### 1. AntGravity 专属增强工具 (9 个)

| 工具名 | 功能描述 |
| :--- | :--- |
| `ag_health_check` | 连通性与软件链环境自检（Python, Java, Git, SDK, EXE 存在性等） |
| `ag_file_list` | 安全沙箱目录列出（白名单：`Obsidian\sync\task`、`dev`、`AndroidProjects`） |
| `ag_file_read` | 文件内容读取（最大支持 512KB） |
| `ag_file_write` | 文件内容安全写入与父目录自动创建 |
| `ag_file_exists` | 目录/文件存在性与类型探测 |
| `ag_powershell` | 核心驱动：非 Admin 权限的任意 PowerShell 执行（支持 pip, git, adb, gradle 等，超时最大 600s） |
| `ag_pptx_read_slide` | PPTX：读取当前活动 PowerPoint 的指定幻灯片中的所有文字和 Shape ID |
| `ag_pptx_fill_text` | PPTX：对指定幻灯片中的 Shape 节点进行文本替换/填充 |
| `ag_pptx_create_slide` | PPTX：在活动幻灯片末尾新建一张幻灯片 |

### 2. windows-mcp 核心桌面交互与 GUI 自动化工具 (18 个)

| 工具名 | 类别 | 功能描述 |
| :--- | :--- | :--- |
| `Click` | 鼠标交互 | 在坐标 `[x, y]` 点击或寻找带有特定文本/ID 的 UI 元素点击 |
| `Type` | 键盘交互 | 在指定位置或焦点输入框模拟物理键盘打字输入文本 |
| `Scroll` | 鼠标交互 | 在指定位置或 UI 元素模拟鼠标滚轮滚动（支持横向/纵向） |
| `Move` | 鼠标交互 | 物理移动光标位置至目标坐标或 UI 元素中心 |
| `Shortcut` | 键盘交互 | 执行复杂的物理键盘快捷键组合（如 `ctrl+c`, `win+r`, `alt+tab`） |
| `Screenshot` | 视觉感知 | 高速截取高清屏幕截图，并通过 UI 元素自动匹配识别 |
| `Snapshot` | 视觉感知 | 截取屏幕并生成当前桌面的完整层次 UI Tree（提取所有可见文本与元素坐标） |
| `Scrape` | 网络辅助 | 直接爬取并解析目标网页的文本数据 |
| `App` | 进程管理 | 启动或激活指定的桌面应用程序并最大化/激活其主窗口 |
| `Process` | 进程管理 | 列出 Windows 系统的运行进程，或按名称/PID 结束进程 |
| `Clipboard` | 系统服务 | 底层读写系统剪贴板，支持复制、剪切、粘帖操作 |
| `Notification` | 系统服务 | 向 Windows 桌面右下角推送系统级 Toast 气泡通知 |
| `Registry` | 系统服务 | 读写 Windows 注册表项（用于读取配置或临时状态） |
| `FileSystem` | 文件系统 | 内置的文件系统读写管理辅助工具 |
| `PowerShell` | 命令行 | 内置的快速命令行执行通道 |
| `MultiSelect` | 组合辅助 | 一键执行对多个文件或 UI 复选框的选中操作 |
| `MultiEdit` | 组合辅助 | 批量对多个表单输入框写入数据 |
| `Wait` | 定时控制 | 显式暂停执行（秒级），常用于等待 GUI 动画渲染 |

---

## 📈 已完成阶段

- [x] **协议选型与跨主机打通**：基于 Starlette app 的 FastMCP StreamableHTTP，结合 `TrustedHostMiddleware`，顺利移除 421 DNS 劫持防护，实现局域网内所有 Host header 的平滑连接。
- [x] **Windows 服务化托管 (NSSM)**：注册 `AntGravityMCP` 系统服务，修正 `PYTHONPATH` 使其能够引用用户下的 Roaming Python 依赖模块，服务状态处于稳定 **Running**。
- [x] **windows-mcp 核心集成**：在 `server.py` 内实现 `mcp_lifespan` 优雅拉起并结束 windows-mcp 的后台 WatchDog 焦点监控，并在 app 中使用 `register_all` 注册了 18 个富交互桌面工具。
- [x] **本地端到端测试 (E2E)**：使用 `test_mcp.py` 成功在 9000 服务上跑通 **8/8 个核心测试步骤**。
- [x] **测试报告归档**：产出详尽的 [hermes-test-report.md](file:///d:/Obsidian/sync/task/antgravity-mcp-server/hermes-test-report.md) 文档。
- [x] **Git 安全沙箱规则**：配置好完整的 `.gitignore` 文件，屏蔽本地垃圾临时文件、Syncthing 同步冲突与 log 日志。

---

## 📋 待处理与后期规划

1. **Android SDK 环境部署**：
   - 检查到 `android_sdk: false`。如后续需执行打包/构建等自动化 Android 开发任务，需手动或使用 PowerShell 安装 Android CLI 命令行组件（`cmdline-tools`），并注册 `ANDROID_HOME`。
2. **应用会话会话 0 隔离问题观测**：
   - 若在后台运行截图工具时发现只能截取黑屏，需要进入 Windows 服务管理器 (`services.msc`) 将 `AntGravityMCP` 服务修改为以本地活动用户（例如 `keche` 或本地管理员）的身份登录，或勾选“允许服务与桌面交互”。

---

## 📁 核心日志与配置文件位置

* **主运行日志**：`D:\Obsidian\sync\task\antgravity-mcp-server\logs\server.log`
* **版本库配置**：`D:\Obsidian\sync\task\antgravity-mcp-server\.gitignore`
* **运行入口文件**：`D:\Obsidian\sync\task\antgravity-mcp-server\server.py`
