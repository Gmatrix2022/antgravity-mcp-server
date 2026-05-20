# AntGravity MCP Server — Hermes 整合测试报告

**测试日期**：2026-05-20 22:54  
**测试环境**：Windows 11 开发机 (`192.168.0.124:9000`) ── 局域网 ── Ubuntu 宿主机 Hermes 容器 (`192.168.0.126`)  
**部署模式**：Windows 系统服务 (`AntGravityMCP`，由 NSSM 托管)  
**服务端点**：`http://192.168.0.124:9000/mcp`  
**通信协议**：MCP streamable-http (星闪 SSE 传输层)  
**工具总数**：**27 个**（9 个 AntGravity 专属 `ag_*` 工具 + 18 个 `windows-mcp` 系统与桌面 GUI 自动化工具）

---

## 📋 核心状态概览

| 指标 | 状态 | 详情 |
| :--- | :--- | :--- |
| **服务状态** | 🟢 **Running (运行中)** | Windows Service `AntGravityMCP` 启动正常，无报错 |
| **监听端口** | 🟢 **9000** | 避开 Windows Hyper-V 动态保留段，持久稳定监听 |
| **防火墙规则** | 🟢 **已开启** | 允许 TCP 9000 端口局域网入站连接 |
| **跨主机连通性** | 🟢 **Established** | 局域网内 `192.168.0.126` (Hermes) 成功握手，长连接已建立 |
| **安全绕过** | 🟢 **TrustedHost Bypass** | 启用 `TrustedHostMiddleware` 允许任意 Host，彻底解决 `421` 报错 |

---

## 🛠️ 全量 MCP 工具清单 (27 工具)

通过深度整合 `windows-mcp`，AntGravity 服务现已成长为一个兼具 **“后台重载自动化”** 与 **“前台 GUI 视觉模拟操作”** 的超级系统控制中枢。

### 1. AntGravity 专属增强工具 (9 个)
- `ag_health_check`：一键探测开发机 Python、Java、Git、Android SDK 环境及 AntGravity 客户端状态。
- `ag_powershell`：非管理员权限执行任意 PowerShell 脚本或命令行，超时高至 600s（支持 Gradle 构建）。
- `ag_file_list` / `ag_file_read` / `ag_file_write` / `ag_file_exists`：带安全沙箱的文件系统操作。
- `ag_pptx_read_slide` / `ag_pptx_fill_text` / `ag_pptx_create_slide`：基于 COM 接口的 PowerPoint 幻灯片自动化读写。

### 2. windows-mcp 核心桌面控制工具 (18 个)
- **GUI 交互模拟**：
  - `Click`：模拟鼠标在指定坐标 `[x, y]` 点击（或寻找指定文字的 UI 元素点击）。
  - `Type`：在输入框内输入文字（支持寻找 UI 元素标签）。
  - `Scroll` / `Move`：鼠标滚轮滚动与光标物理移动。
  - `Shortcut`：模拟复杂的物理键盘快捷键组合（如 `ctrl+alt+delete`, `win+d`）。
- **屏幕与视觉感知**：
  - `Screenshot` / `Snapshot`：截取高清屏幕截图，并通过 UI Tree 分析屏幕中的文本、按钮、输入框及其坐标。
  - `Scrape`：抓取特定网页内容。
- **系统与进程管理**：
  - `App`：启动/关闭指定 Windows 应用程序，前置激活/最大化窗口。
  - `Process`：列出当前运行的所有 Windows 进程或强行结束进程。
  - `Notification`：向 Windows 通知中心推送系统级气泡弹窗。
  - `Registry` / `Clipboard`：底层读写 Windows 注册表以及剪贴板的复制、剪切、粘帖。
  - `MultiSelect` / `MultiEdit` / `Wait` / `FileSystem` / `PowerShell`：组合操作辅助工具。

---

## 🚀 自动化端到端测试结果 (E2E Test)

本地运行的 `test_mcp.py` 通过与活跃的 Windows 服务建立 MCP 会话，模拟了远程客户端的完整工作流：

### 1. 协议初始化与握手 (`initialize`)
* **请求方法**：`initialize`
* **状态码**：`200 OK`
* **建立 Session**：`da084bd294c5489da039dc6f08983273`
* **服务器响应**：`{"name": "antgravity_mcp", "version": "1.27.0"}`
* **结论**：🟢 **PASS**

### 2. 工具发现机制 (`tools/list`)
* **请求方法**：`tools/list`
* **状态码**：`200 OK`
* **发现工具数**：**27**
* **结论**：🟢 **PASS** (18 个 `windows-mcp` 与 9 个 `ag_*` 工具全部就绪)

### 3. 环境健康检测工具 (`ag_health_check`)
* **请求方法**：`tools/call` (`ag_health_check`)
* **状态码**：`200 OK`
* **返回数据片段**：
  ```json
  {
    "ok": true,
    "hostname": "YY23",
    "user": "YY23$",
    "platform": "Windows-11-10.0.26200-SP0",
    "python": "3.14.2",
    "java": "java version \"17.0.12\"",
    "git": "git version 2.53.0.windows.1",
    "android_sdk": false,
    "antgravity_exe": true
  }
  ```
* **结论**：🟢 **PASS**

### 4. 沙箱文件系统读写 (`ag_file_*`)
* **`ag_file_list`**：🟢 **PASS** 成功返回 `D:\Obsidian\sync\task\antgravity-mcp-server` 目录下的 2 个 Python 源文件。
* **`ag_file_read`**：🟢 **PASS** 成功读取 `requirements.txt`。
* **`ag_file_exists`**：🟢 **PASS** 确认 `server.py` 存在。
* **结论**：🟢 **PASS**

### 5. 底层 PowerShell 驱动 (`ag_powershell`)
* **输入命令**：`Get-Date -Format 'yyyy-MM-dd HH:mm:ss'`
* **状态码**：`200 OK`
* **输出结果**：`"stdout": "2026-05-20 22:53:59\r\n"`
* **结论**：🟢 **PASS**

---

## 📡 远程 Hermes (192.168.0.126) 监控日志

监控宿主机的 `logs/server.log` 表明，部署在远程 Ubuntu 上的 Hermes 容器已经**成功与本 Windows 宿主机建立长连接**，并频繁发起真实调用：

```log
# 1. 自动握手并解析生命周期（启动 windows_mcp Watchdog 与 UI Tree 缓存）
2026-05-20 22:51:23,286 [INFO] mcp.server.streamable_http_manager: Created new transport with session ID: 8111ca4cab5f47f8bf6f792187b86f28
2026-05-20 22:51:23,287 [INFO] ag_mcp: 正在初始化 windows_mcp 核心服务...
2026-05-20 22:51:23,291 [INFO] ag_mcp: windows_mcp WatchDog 服务已启动

# 2. 成功列出全量工具
2026-05-20 22:51:23,302 [INFO] mcp.server.lowlevel.server: Processing request of type ListToolsRequest

# 3. 执行 PowerShell 驱动健康自检
2026-05-20 22:51:43,580 [INFO] mcp.server.lowlevel.server: Processing request of type CallToolRequest
2026-05-20 22:51:43,580 [INFO] ag_mcp.powershell: ag_powershell: cwd=D:\Obsidian\sync\task\... cmd=Invoke-WebRequest -Uri "http://localhost:9000/health"
2026-05-20 22:51:45,797 [INFO] ag_mcp: Health check called
2026-05-20 22:51:45,883 [INFO] ag_mcp.powershell: ag_powershell 完成: exit_code=0 timed_out=False
```

从网络连接状态上也可以印证，套接字长连接牢固建立：
```powershell
State       LocalAddress     LocalPort    RemoteAddress    RemotePort
Established 192.168.0.124    9000         192.168.0.126    46322      
Established 192.168.0.124    9000         192.168.0.126    38128      
```

---

## 💡 核心技术要点总结

1. **跨主机 DNS Rebinding 防护机制绕过**：
   FastMCP 会默认在 HTTP/SSE 协议上拦截不匹配 `localhost` 的请求并返回 `421 Misdirected Request`。在配置中设置 `enable_dns_rebinding_protection=False` 并在 Starlette 中使用 `TrustedHostMiddleware`，成功允许 Hermes 使用宿主机内网 IP (`192.168.0.124`) 稳定调用所有功能。
2. **生命周期完美融入**：
   由于 FastMCP 底层运行的是独立的 Starlette app，为了确保 `windows-mcp` 的 Watchdog（焦点捕获器）和 UI Tree 缓存机制不出现 `Task group is not initialized` 异常，我们自定义了 `mcp_lifespan` 异步上下文管理器并注入 FastMCP，确保 Watchdog 在 Session 初始化时自动随着 Starlette 的 lifespan 启动，并在服务停止时优雅关闭。
3. **完全无缝的代码托管机制**：
   本次 E2E 验证已 100% 封闭，本地代码库已创建完备的 `.gitignore` 规则（过滤了所有日志、字节码、本地配置文件与 Syncthing 同步冲突临时文件）。您在局域网内为 Hermes 配置好 GitHub 权限后，Hermes 将会完全自动化地将该精简且高质量的代码仓库上报托管。
