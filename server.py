#!/usr/bin/env python3
"""
AntGravity MCP Server — Phase 0 + Phase 1

监听 http://0.0.0.0:9000
- /health         → Phase 0 健康检查 HTTP 端点
- /mcp            → FastMCP StreamableHTTP 端点（Phase 1 MCP 工具）

工具清单（Phase 1）：
  ag_health_check  ag_file_read  ag_file_write  ag_file_list
  ag_file_exists   ag_powershell
"""

import json
import logging
import os
import platform
import shutil
import socket
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

# ── 日志配置 ──────────────────────────────────────────────────────────────
LOG_DIR = Path(r"D:\Obsidian\sync\task\antgravity-mcp-server\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "server.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("ag_mcp")

# ── 导入工具模块 ──────────────────────────────────────────────────────────
from tools.filesystem_tools import (
    FileReadInput, FileWriteInput, FileListInput, FileExistsInput,
    ag_file_read, ag_file_write, ag_file_list, ag_file_exists,
)
from tools.powershell_tools import PowerShellInput, ag_powershell

# ── windows_mcp 核心服务整合与生命周期 ─────────────────────────────────────
desktop_instance = None
watchdog_instance = None
analytics_instance = None

def get_desktop():
    return desktop_instance

def get_analytics():
    return analytics_instance

@asynccontextmanager
async def mcp_lifespan(app: FastMCP):
    """管理 windows_mcp 后台服务的生命周期（WatchDog, Analytics, Desktop）"""
    global desktop_instance, watchdog_instance, analytics_instance
    logger.info("正在初始化 windows_mcp 核心服务...")
    
    from windows_mcp.analytics import PostHogAnalytics
    from windows_mcp.desktop.service import Desktop
    from windows_mcp.watchdog.service import WatchDog
    
    if os.getenv("ANONYMIZED_TELEMETRY", "true").lower() != "false":
        analytics_instance = PostHogAnalytics()
    desktop_instance = Desktop()
    watchdog_instance = WatchDog()
    
    # 设置 watchdog 焦点变化回调，使 UI Tree 缓存机制生效
    watchdog_instance.set_focus_callback(desktop_instance.tree.on_focus_change)
    
    try:
        watchdog_instance.start()
        logger.info("windows_mcp WatchDog 服务已启动")
        yield
    finally:
        logger.info("正在关闭 windows_mcp 服务...")
        if watchdog_instance:
            watchdog_instance.stop()
            logger.info("WatchDog 服务已停止")
        if analytics_instance:
            await analytics_instance.close()
            logger.info("Analytics 已关闭")

# ── FastMCP 实例 ──────────────────────────────────────────────────────────
# 禁用 MCP SDK 内置的 DNS rebinding 保护（enable_dns_rebinding_protection=False）
# 原因：Hermes 容器通过 IP 访问时 Host: 192.168.0.124:9000，默认会被拒绝（421）
from mcp.server.transport_security import TransportSecuritySettings
mcp = FastMCP(
    "antgravity_mcp",
    lifespan=mcp_lifespan,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    ),
)

# 注册 windows_mcp 的 18 个系统控制工具
from windows_mcp.tools import register_all
register_all(mcp, get_desktop=get_desktop, get_analytics=get_analytics)
logger.info("windows_mcp 的 18 个核心 OS 交互工具已成功注册至 antgravity_mcp 实例！")

# ── 注册 Phase 5 新工具 ──────────────────────────────────────────────────────
from tools.stream_tools import (
    ag_record_step, ag_get_current_status, ag_get_step_history, ag_accept_action
)
from tools.kanban_tools import (
    ag_kanban_create, ag_kanban_update, ag_kanban_comment, ag_kanban_complete,
    ag_kanban_list, ag_kanban_get
)

# ── 注册 Stream 相关的 4 个工具 ──
mcp.tool(name="ag_record_step")(ag_record_step)
mcp.tool(name="ag_get_current_status")(ag_get_current_status)
mcp.tool(name="ag_get_step_history")(ag_get_step_history)
mcp.tool(name="ag_accept_action")(ag_accept_action)

# ── 注册 Kanban 相关的 6 个工具 ──
mcp.tool(name="ag_kanban_create")(ag_kanban_create)
mcp.tool(name="ag_kanban_update")(ag_kanban_update)
mcp.tool(name="ag_kanban_comment")(ag_kanban_comment)
mcp.tool(name="ag_kanban_complete")(ag_kanban_complete)
mcp.tool(name="ag_kanban_list")(ag_kanban_list)
mcp.tool(name="ag_kanban_get")(ag_kanban_get)

logger.info("Phase 5 流与看板管理的 10 个新工具已成功注册至 antgravity_mcp 实例！")


# ── 辅助：环境探测 ────────────────────────────────────────────────────────
def _detect_version(cmd: list[str]) -> Optional[str]:
    """静默运行命令，返回首行输出或 None。"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5
        )
        first = result.stdout.strip().splitlines()
        return first[0] if first else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  Phase 1 MCP 工具
# ═══════════════════════════════════════════════════════════════════════════

# ── ag_health_check ───────────────────────────────────────────────────────

@mcp.tool(
    name="ag_health_check",
    annotations={
        "title": "AntGravity MCP Server Health Check",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def ag_health_check() -> str:
    """
    【优先调用】检查 AntGravity Windows 开发机的连通性与软件环境。

    在执行任何 Windows 侧任务之前，应先调用此工具以确认：
    1. MCP Server 运行正常（ok: true）
    2. 目标软件已安装（python/java/git/android_sdk）
    3. 获取主机信息用于后续任务规划

    典型使用场景：
    - 开始 Android 构建前：确认 java + android_sdk 均已就绪
    - 开始 Python 任务前：确认 python 版本
    - 诊断工具链问题时：全面检查环境

    Returns:
        str: JSON 格式结果，包含：
            - ok (bool): 服务是否正常
            - hostname (str): Windows 主机名
            - user (str): 当前 Windows 用户（keche）
            - cwd (str): 服务器工作目录
            - platform (str): Windows 版本信息
            - python (str): Python 版本（用于 ag_powershell 中 python 命令）
            - java (str|null): Java 版本（null 表示未安装，Android 构建需要）
            - git (str|null): Git 版本（null 表示未安装）
            - android_sdk (bool): ANDROID_HOME/ANDROID_SDK_ROOT 是否已设置
            - android_sdk_path (str|null): Android SDK 路径
            - antgravity_exe (bool): AntGravity.exe 桌面客户端是否存在
    """
    java_ver = _detect_version(["java", "-version"])
    if java_ver is None:
        # java -version 输出到 stderr
        try:
            r = subprocess.run(
                ["java", "-version"], capture_output=True, text=True, timeout=5
            )
            java_ver = r.stderr.strip().splitlines()[0] if r.stderr.strip() else None
        except Exception:
            java_ver = None

    git_ver = _detect_version(["git", "--version"])
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    antgravity_exe = Path(
        r"C:\Users\keche\AppData\Local\Programs\Antigravity\Antigravity.exe"
    ).exists()

    result = {
        "ok": True,
        "hostname": socket.gethostname(),
        "user": os.environ.get("USERNAME", os.environ.get("USER", "unknown")),
        "cwd": str(Path.cwd()),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "java": java_ver,
        "git": git_ver,
        "android_sdk": bool(android_home),
        "android_sdk_path": android_home,
        "antgravity_exe": antgravity_exe,
    }
    logger.info("ag_health_check 调用成功")
    return json.dumps(result, ensure_ascii=False)


# ── ag_file_read ──────────────────────────────────────────────────────────

@mcp.tool(
    name="ag_file_read",
    annotations={
        "title": "Read File",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def tool_file_read(
    path: str = Field(..., description="Windows 绝对路径，如 D:\\dev\\myapp\\src\\main.py"),
    encoding: str = Field(default="utf-8", description="文件编码，默认 utf-8，中文文件可能需要 gbk"),
) -> str:
    """
    读取 Windows 文件系统中指定文件的完整内容。

    【可访问目录（白名单）】
    - D:\\Obsidian\\sync\\task\\   → 任务文件、笔记、MCP 项目代码
    - D:\\dev\\                  → Windows 开发项目（Web/Python/工具）
    - D:\\AndroidProjects\\      → Android 应用源码（Kotlin/Java/Gradle）

    【限制】
    - 文件大小上限：512 KB（超出返回 error，请改用 ag_powershell 分段读取）
    - 拒绝访问：C:\\Windows\\, ~/.hermes/.env 等敏感路径

    【典型使用场景】
    - 读取源代码文件进行审查或修改
    - 读取配置文件（build.gradle, package.json, requirements.txt）
    - 读取日志文件（≤512KB）
    - 读取本 MCP 项目的 STATUS.md / HERMES-TEST.md 等文档

    Args:
        path: Windows 绝对路径
        encoding: 文件编码（默认 utf-8）

    Returns:
        str: JSON {ok:true, path, size_bytes, content} 或 {ok:false, error}
    """
    return await ag_file_read(FileReadInput(path=path, encoding=encoding))


# ── ag_file_write ─────────────────────────────────────────────────────────

@mcp.tool(
    name="ag_file_write",
    annotations={
        "title": "Write File",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def tool_file_write(
    path: str = Field(..., description="目标 Windows 路径，如 D:\\Obsidian\\sync\\task\\report.md"),
    content: str = Field(..., description="要写入的文本内容"),
    encoding: str = Field(default="utf-8", description="文件编码，默认 utf-8"),
    overwrite: bool = Field(default=True, description="是否覆盖已有文件（默认 True）"),
) -> str:
    """
    将文本内容写入 Windows 文件系统（自动创建父目录）。

    【可写入目录（白名单）】
    - D:\\Obsidian\\sync\\task\\   → 任务输出、测试报告、生成文件
    - D:\\dev\\                  → 项目代码、配置文件
    - D:\\AndroidProjects\\      → Android 源码、资源文件

    【典型使用场景】
    - 将生成的代码写入源文件
    - 保存任务执行报告（如 hermes-test-report.md）
    - 修改配置文件（build.gradle, .env, settings.json）
    - 创建新文件或覆盖现有文件

    【注意】
    - 仅支持文本文件（UTF-8 或指定编码）
    - 二进制文件请改用 ag_powershell 处理
    - overwrite=False 时若文件已存在会返回 error

    Args:
        path: 目标 Windows 路径
        content: 要写入的文本内容
        encoding: 编码（默认 utf-8）
        overwrite: 是否覆盖已有文件（默认 True）

    Returns:
        str: JSON {ok:true, path, bytes_written} 或 {ok:false, error}
    """
    return await ag_file_write(FileWriteInput(path=path, content=content, encoding=encoding, overwrite=overwrite))


# ── ag_file_list ──────────────────────────────────────────────────────────

@mcp.tool(
    name="ag_file_list",
    annotations={
        "title": "List Directory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def tool_file_list(
    path: str = Field(..., description="目录路径，如 D:\\AndroidProjects\\MyApp"),
    pattern: str = Field(default="*", description="glob 过滤模式，如 *.py"),
    recursive: bool = Field(default=False, description="是否递归子目录（默认 False，大项目建议 False）"),
) -> str:
    """
    列出 Windows 目录中的文件和子目录，支持 glob 过滤和递归。

    【可访问目录（白名单）】
    - D:\\Obsidian\\sync\\task\\   → 各类任务项目目录
    - D:\\dev\\                  → 开发项目
    - D:\\AndroidProjects\\      → Android 项目

    【典型使用场景】
    - 探索项目结构（pattern="*", recursive=False）
    - 查找特定类型文件（pattern="*.kt" 找 Kotlin 源文件）
    - 递归列出所有 Python 文件（pattern="*.py", recursive=True）
    - 检查构建产物（pattern="*.apk", recursive=True）

    【常用 pattern 示例】
    - "*"       → 所有文件和目录
    - "*.py"    → Python 文件
    - "*.kt"    → Kotlin 文件
    - "*.apk"   → Android 安装包
    - "*.md"    → Markdown 文档
    - "*.gradle" → Gradle 构建文件

    【限制】最多返回 500 条，超出部分截断

    Args:
        path: 目录路径
        pattern: glob 过滤模式（默认 "*"）
        recursive: 是否递归子目录（默认 False）

    Returns:
        str: JSON {ok, path, pattern, count, entries:[{name, path, type, size_bytes}]}
    """
    return await ag_file_list(FileListInput(path=path, pattern=pattern, recursive=recursive))


# ── ag_file_exists ────────────────────────────────────────────────────────

@mcp.tool(
    name="ag_file_exists",
    annotations={
        "title": "Check Path Exists",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def tool_file_exists(
    path: str = Field(..., description="要检查的 Windows 路径（白名单目录内）"),
) -> str:
    """
    检查 Windows 路径是否存在，并返回其类型。

    【典型使用场景】
    - 在 ag_file_read 之前确认文件存在（避免 error）
    - 在 ag_file_write 之前确认目标路径状态
    - 检查构建产物是否生成（如 APK 文件）
    - 验证工具链路径（如 Android SDK 目录）

    【返回的 type 值】
    - "file" → 是一个文件
    - "dir"  → 是一个目录
    - "none" → 路径不存在

    Args:
        path: 要检查的 Windows 路径

    Returns:
        str: JSON {ok:true, path, exists:bool, type:"file"|"dir"|"none"}
             若路径在黑名单/白名单外：{ok:false, error}
    """
    return await ag_file_exists(FileExistsInput(path=path))


# ── ag_powershell ─────────────────────────────────────────────────────────

@mcp.tool(
    name="ag_powershell",
    annotations={
        "title": "Execute PowerShell",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def tool_powershell(
    command: str = Field(..., description="PowerShell 命令或多行脚本（最大 8192 字符）", min_length=1, max_length=8192),
    timeout: int = Field(default=120, description="超时秒数（1-600），默认 120，Gradle 构建建议 600", ge=1, le=600),
    cwd: Optional[str] = Field(default=None, description="工作目录（可选，默认 D:\\Obsidian\\sync\\task\\antgravity-mcp-server）"),
) -> str:
    """
    在 Windows 上执行任意 PowerShell 命令或脚本（非管理员权限）。

    这是功能最强的工具，覆盖文件工具无法处理的所有 Windows 操作。
    执行环境：PowerShell 5.1+，-NonInteractive -NoProfile -ExecutionPolicy Bypass

    【已确认可用的命令行工具】
    - python / pip          → Python 脚本执行、包安装
    - git                   → 版本控制（status/add/commit/push/pull/clone）
    - java / javac          → Java 编译与运行
    - gradle / gradlew      → Android/Java 构建（assembleDebug, test, clean）
    - adb                   → Android Debug Bridge（devices, install, logcat）
    - node / npm / npx      → Node.js 运行、前端构建
    - docker                → Docker 容器管理
    - curl / Invoke-WebRequest → HTTP 请求
    - Get-* / Set-* / ...   → PowerShell 内置 cmdlet

    【典型使用场景与示例】
    # Android 开发
    "cd D:\\AndroidProjects\\MyApp; .\\gradlew assembleDebug"
    "adb devices"
    "adb install D:\\AndroidProjects\\MyApp\\app\\build\\outputs\\apk\\debug\\app-debug.apk"

    # Python 项目
    "cd D:\\dev\\myproject; python main.py"
    "pip install -r D:\\dev\\myproject\\requirements.txt"

    # Git 操作
    "cd D:\\dev\\myrepo; git status; git log --oneline -5"
    "cd D:\\dev\\myrepo; git add -A; git commit -m 'auto commit'"

    # 系统信息
    "Get-Date; $env:USERNAME; $env:COMPUTERNAME"
    "Get-Process | Sort-Object CPU -Descending | Select-Object -First 10"
    "Get-ChildItem D:\\dev -Recurse -Filter *.py | Measure-Object"

    # 网络
    "Invoke-WebRequest -Uri 'http://192.168.0.124:9000/health' -UseBasicParsing"

    【安全黑名单（以下命令会被拒绝）】
    Remove-Item -Recurse C:\\, Format-Volume, Stop-Computer,
    Restart-Computer, bcdedit, reg delete HKLM, net user

    【输出限制】返回最后 200 行，超长输出自动截断
    【超时】默认 120s，构建任务建议设置 timeout=600

    Args:
        command: PowerShell 命令或多行脚本（最大 8192 字符）
        timeout: 超时秒数（默认 120，最大 600）
        cwd: 工作目录（可选）

    Returns:
        str: JSON {ok:bool, exit_code:int, stdout:str, stderr:str, timed_out:bool}
             ok=true 表示 exit_code==0 且未超时
    """
    return await ag_powershell(PowerShellInput(command=command, timeout=timeout, cwd=cwd))


# ── ag_pptx_tools ─────────────────────────────────────────────────────────

from tools.pptx_tools import PowerPointController

@mcp.tool(
    name="ag_pptx_read_slide",
    annotations={
        "title": "Read PPTX Slide",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def tool_pptx_read_slide(
    slide_index: int = Field(..., description="Slide index (1-based)")
) -> str:
    """Reads all text shapes from a specific slide in the currently active PowerPoint presentation."""
    ctrl = PowerPointController()
    res = ctrl.read_slide(slide_index)
    return json.dumps(res, ensure_ascii=False)

@mcp.tool(
    name="ag_pptx_fill_text",
    annotations={
        "title": "Fill PPTX Text",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def tool_pptx_fill_text(
    slide_index: int = Field(..., description="Slide index (1-based)"),
    shape_id: int = Field(..., description="Shape ID on the slide"),
    new_text: str = Field(..., description="New text to fill in the shape")
) -> str:
    """Fills a specific shape on a specific slide with new_text in the currently active PowerPoint presentation."""
    ctrl = PowerPointController()
    res = ctrl.fill_text(slide_index, shape_id, new_text)
    return json.dumps(res, ensure_ascii=False)

@mcp.tool(
    name="ag_pptx_create_slide",
    annotations={
        "title": "Create PPTX Slide",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def tool_pptx_create_slide(
    layout_index: int = Field(default=12, description="Layout index (12 = blank)")
) -> str:
    """Creates a new slide at the end of the currently active PowerPoint presentation."""
    ctrl = PowerPointController()
    res = ctrl.create_slide(layout_index)
    return json.dumps(res, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════════════
#  应用入口：使用 FastMCP 的 Starlette app 作为基础，注入 /health 路由
#
#  关键：FastMCP.streamable_http_app() 返回 Starlette 实例，其 lifespan 包含
#  StreamableHTTPSessionManager.run()（初始化 task group），必须保留。
#  直接在该 Starlette app 上添加自定义路由，而不是 mount 到外部 FastAPI。
# ═══════════════════════════════════════════════════════════════════════════

from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.routing import Route

async def health_endpoint(request: Request):
    """Phase 0 健康检查端点"""
    logger.info("Health check called")
    return JSONResponse({"ok": True, "service": "antgravity-mcp", "version": "0.1.0", "port": 9000})


# 获取 FastMCP Starlette app（含正确的 lifespan/task group）
app = mcp.streamable_http_app()

# 允许任意 Host header（修复 Hermes 容器跨主机访问 421 问题）
# 容器内请求携带 Host: 192.168.0.124:9000，Starlette 默认拒绝导致 421
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# 在现有路由列表头部插入 /health 路由
app.routes.insert(0, Route("/health", endpoint=health_endpoint, methods=["GET"]))

logger.info("AntGravity MCP Server 路由配置完成: /health + /mcp（TrustedHostMiddleware 已启用）")


# ═══════════════════════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=9000,
        log_level="info",
        reload=False,
    )

