"""
AntGravity MCP Server - PowerShell Tools

以非管理员权限执行 PowerShell 命令，带超时控制和命令黑名单过滤。
"""

import asyncio
import json
import logging
import re
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger("ag_mcp.powershell")

# ── 默认工作目录 ─────────────────────────────────────────────────────────
DEFAULT_CWD = r"D:\Obsidian\sync\task\antgravity-mcp-server"

# ── 输出截断 ─────────────────────────────────────────────────────────────
MAX_OUTPUT_LINES = 200

# ── 危险命令黑名单（正则，大小写不敏感）─────────────────────────────────
BLACKLIST_PATTERNS: list[re.Pattern] = [
    re.compile(r"Remove-Item\s+.*-Recurse\s+[A-Za-z]:\\", re.IGNORECASE),
    re.compile(r"Format-Volume", re.IGNORECASE),
    re.compile(r"\bStop-Computer\b", re.IGNORECASE),
    re.compile(r"\bRestart-Computer\b", re.IGNORECASE),
    re.compile(r"\bbcdedit\b", re.IGNORECASE),
    re.compile(r"reg\s+delete\s+HKLM", re.IGNORECASE),
    re.compile(r"\bnet\s+user\b", re.IGNORECASE),
    re.compile(r"rm\s+-[rRf]+\s+[A-Za-z]:\\", re.IGNORECASE),
    re.compile(r"del\s+/[sS]\s+[A-Za-z]:\\", re.IGNORECASE),
]


def _check_blacklist(command: str) -> Optional[str]:
    """返回被匹配的黑名单模式描述，若无危险则返回 None。"""
    for pattern in BLACKLIST_PATTERNS:
        if pattern.search(command):
            return pattern.pattern
    return None


def _tail_lines(text: str, n: int) -> str:
    lines = text.splitlines()
    if len(lines) > n:
        truncated = len(lines) - n
        return f"... （已截断 {truncated} 行）\n" + "\n".join(lines[-n:])
    return text


# ── Pydantic 输入模型 ─────────────────────────────────────────────────────

class PowerShellInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    command: str = Field(
        ...,
        description="要执行的 PowerShell 命令或脚本内容",
        min_length=1,
        max_length=8192,
    )
    timeout: int = Field(
        default=120,
        description="超时秒数（1-600），默认 120",
        ge=1,
        le=600,
    )
    cwd: Optional[str] = Field(
        default=None,
        description=f"工作目录，默认 {DEFAULT_CWD}",
    )


# ── 工具实现 ──────────────────────────────────────────────────────────────

async def ag_powershell(params: PowerShellInput) -> str:
    """
    在 Windows 上执行 PowerShell 命令。

    安全约束：
    - 黑名单过滤高危命令
    - 超时强制终止（params.timeout 秒）
    - 默认工作目录限制在任务目录
    - 输出截取最后 200 行

    Args:
        params.command: PowerShell 命令或脚本
        params.timeout: 超时秒数（默认 120）
        params.cwd: 工作目录（可选）

    Returns:
        str: JSON {ok, exit_code, stdout, stderr, timed_out, error?}
    """
    # 黑名单检查
    blocked = _check_blacklist(params.command)
    if blocked:
        logger.warning("ag_powershell 被黑名单拒绝: pattern=%s", blocked)
        return json.dumps({
            "ok": False,
            "error": f"命令被安全策略拒绝（匹配高危模式：{blocked}）"
        })

    cwd = params.cwd or DEFAULT_CWD
    logger.info("ag_powershell: cwd=%s timeout=%ds cmd=%.120s", cwd, params.timeout, params.command)

    # 构建 PowerShell 调用：使用 -NonInteractive -NoProfile 减少干扰
    ps_args = [
        "powershell.exe",
        "-NonInteractive",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", params.command,
    ]

    timed_out = False
    try:
        proc = await asyncio.create_subprocess_exec(
            *ps_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=params.timeout
            )
        except asyncio.TimeoutError:
            timed_out = True
            proc.kill()
            stdout_bytes, stderr_bytes = await proc.communicate()

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        exit_code = proc.returncode if not timed_out else -1

        result = {
            "ok": not timed_out and exit_code == 0,
            "exit_code": exit_code,
            "stdout": _tail_lines(stdout, MAX_OUTPUT_LINES),
            "stderr": _tail_lines(stderr, MAX_OUTPUT_LINES),
            "timed_out": timed_out,
        }
        if timed_out:
            result["error"] = f"命令超时（{params.timeout}s），已强制终止"

        logger.info("ag_powershell 完成: exit_code=%s timed_out=%s", exit_code, timed_out)
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error("ag_powershell 异常: %s", e)
        return json.dumps({"ok": False, "error": f"启动失败：{e}"})
