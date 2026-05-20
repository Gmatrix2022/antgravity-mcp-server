# 实施方案 — 整合 windows-mcp (系统控制) 工具集

我们将把开源项目 `windows-mcp` (由 `CursorTouch` 团队维护) 的整套 Windows 桌面自动化工具，深度整合进现有的 `AntGravity` MCP 服务中。

这将使远程 Hermes 客户端（以及连接到 `9000` 端口的其他 MCP 客户端）不仅能运行 PowerShell 和管理文件，还能获得以下高级能力：
1. **感知屏幕状态**：`Snapshot`（截屏并智能提取所有 UI 控件的 ID/坐标/树形结构）、`Screenshot`（快速截屏）。
2. **硬件级模拟交互**：`Click`（鼠标左/右/中键点击/双击）、`Type`（文本输入/清除/追加/回车）、`Scroll`（鼠标滚轮滚动）、`Move`（移动光标/拖拽拖放）、`Shortcut`（执行如 `alt+tab`、`ctrl+c`、`win`、`win+r` 等全局快捷键）。
3. **窗口与程序管理**：`App`（启动指定程序、聚焦指定窗口、调整窗口大小与位置）。
4. **系统核心交互**：`Clipboard`（读写系统剪贴板）、`Notification`（发送系统 Toast 横幅通知）、`Process`（列出/结束运行进程）、`Registry`（读写 Windows 注册表）。

---

## 需用户知悉与确认事项

> [!IMPORTANT]
> - **统一端口与服务**：我们将把所有工具（包括现有的 9 个 `ag_*` 工具，以及 `windows-mcp` 的 18 个工具）托管在**同一个 `9000` 端口服务**下。您无需再额外维护和配置其他后台服务。
> - **交互式桌面运行权限**：由于硬件键鼠模拟和截屏需要与当前活跃的用户桌面交互，服务必须具备桌面的交互权限。如果目前以 `LocalSystem` 账户运行遇到权限壁垒（例如截屏全黑或无法操作某些应用），我们后续可以将 `AntGravityMCP` 服务的启动账户直接指定为您的本地账户 `keche`（需要输入您的 Windows 密码，或采用其他启动方式）。

---

## 拟进行的修改

### server.py 主程序

#### [MODIFY] [server.py](file:///d:/Obsidian/sync/task/antgravity-mcp-server/server.py)
我们将对主入口文件 `server.py` 进行以下修改：
1. 导入 `windows-mcp` 核心模块 (`PostHogAnalytics`, `Desktop`, `WatchDog`, `register_all`)。
2. 编写 `mcp_lifespan` 异步上下文管理器，在 MCP 启动和退出时安全管理 WatchDog 后台监听、UI 缓存与分析模块的生命周期。
3. 实例化 `FastMCP` 时传入该 lifespan。
4. 调用 `register_all(mcp, ...)` 完成全部系统控制工具的一键式无缝注册。

核心代码拟修改如下：

```python
# ── windows_mcp 整合生命周期与服务 ─────────────────────────────────────────
import os
from contextlib import asynccontextmanager

desktop_instance = None
watchdog_instance = None
analytics_instance = None

def get_desktop():
    return desktop_instance

def get_analytics():
    return analytics_instance

@asynccontextmanager
async def mcp_lifespan(app: FastMCP):
    """管理 windows_mcp 的后台服务生命周期（WatchDog, Analytics, Desktop）"""
    global desktop_instance, watchdog_instance, analytics_instance
    logger.info("正在初始化 windows_mcp 核心服务...")
    
    from windows_mcp.analytics import PostHogAnalytics
    from windows_mcp.desktop.service import Desktop
    from windows_mcp.watchdog.service import WatchDog
    
    if os.getenv("ANONYMIZED_TELEMETRY", "true").lower() != "false":
        analytics_instance = PostHogAnalytics()
    desktop_instance = Desktop()
    watchdog_instance = WatchDog()
    
    # 设置 watchdog 焦点变化回调，使 UI Tree 缓存与焦点捕获生效
    watchdog_instance.set_focus_callback(desktop_instance.tree.on_focus_change)
    
    try:
        watchdog_instance.start()
        logger.info("windows_mcp WatchDog 服务启动成功")
        yield
    finally:
        logger.info("正在关闭 windows_mcp 服务...")
        if watchdog_instance:
            watchdog_instance.stop()
            logger.info("WatchDog 服务已停止")
        if analytics_instance:
            await analytics_instance.close()
            logger.info("Analytics 已关闭")
```

将 `FastMCP` 实例化更新为：
```python
mcp = FastMCP(
    "antgravity_mcp",
    lifespan=mcp_lifespan,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    ),
)

# 注册 windows_mcp 模块内全部 18 个工具
from windows_mcp.tools import register_all
register_all(mcp, get_desktop=get_desktop, get_analytics=get_analytics)
logger.info("windows_mcp 的 18 个核心 OS 交互工具已注册至 antgravity_mcp 实例！")
```

---

## 验证与测试方案

### 自动化测试
1. **静态语法与导入检验**：
   在部署前运行，确保修改无任何导入或语法错误：
   ```powershell
   & "C:\Users\keche\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c "import server; print('Server import verification successful!')"
   ```
2. **工具列表完整度检测**：
   验证 9 个 `ag_*` 与 18 个系统控制工具是否在同一个实例下正常列出：
   ```powershell
   & "C:\Users\keche\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c "import asyncio; import server; print([t.name for t in asyncio.run(server.mcp.list_tools())])"
   ```

### 手动验证
1. **服务平滑升级**：
   重启 Windows 上的 `AntGravityMCP` 系统服务，并持续观察运行日志：
   ```powershell
   Restart-Service AntGravityMCP
   Get-Content -Tail 50 -Path d:\Obsidian\sync\task\antgravity-mcp-server\logs\service.log
   ```
2. **HTTP 健康检验**：
   向服务端点发起 HTTP 请求，验证服务在 `9000` 端口健康响应：
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:9000/health" -UseBasicParsing
   ```
3. **跨主机可用性检验**：
   在 `192.168.0.126` 的 Ubuntu 容器里，利用 `curl` 进行测试，检查跨主机握手是否正常：
   ```bash
   curl -s http://192.168.0.124:9000/health
   ```
