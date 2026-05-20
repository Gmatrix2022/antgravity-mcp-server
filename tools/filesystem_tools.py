"""
AntGravity MCP Server - Filesystem Tools

路径限制在白名单目录内，拒绝访问敏感路径。
"""

import os
import json
import fnmatch
import logging
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

logger = logging.getLogger("ag_mcp.filesystem")

# ── 路径白名单 / 黑名单 ──────────────────────────────────────────────────
ALLOWED_ROOTS: List[str] = [
    r"D:\Obsidian\sync\task",
    r"D:\dev",
    r"D:\AndroidProjects",
]

DENIED_PATHS: List[str] = [
    r"C:\Users\keche\.hermes\.env",
    r"C:\ProgramData\ssh",
    r"C:\Windows",
]

MAX_FILE_BYTES = 512 * 1024   # 512 KB 读取上限
MAX_OUTPUT_LINES = 500         # 列表工具最多返回条数


def _normalize(path: str) -> Path:
    """解析、展开并返回绝对路径。"""
    return Path(os.path.expandvars(path)).resolve()


def _is_allowed(path: str) -> tuple[bool, str]:
    """检查路径是否在白名单内且不在黑名单内。"""
    p = _normalize(path)
    # 黑名单优先
    for denied in DENIED_PATHS:
        dn = _normalize(denied)
        if str(p).lower().startswith(str(dn).lower()):
            return False, f"路径被安全策略拒绝：{p}"
    # 白名单
    for root in ALLOWED_ROOTS:
        rn = _normalize(root)
        try:
            p.relative_to(rn)
            return True, ""
        except ValueError:
            continue
    return False, f"路径不在允许范围内（白名单：{ALLOWED_ROOTS}）：{p}"


# ── Pydantic 输入模型 ─────────────────────────────────────────────────────

class FileReadInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    path: str = Field(..., description="要读取的文件路径，必须在允许目录内")
    encoding: str = Field(default="utf-8", description="文件编码，默认 utf-8")


class FileWriteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    path: str = Field(..., description="要写入的文件路径，必须在允许目录内")
    content: str = Field(..., description="写入的文本内容")
    encoding: str = Field(default="utf-8", description="文件编码，默认 utf-8")
    overwrite: bool = Field(default=True, description="是否允许覆盖已有文件")


class FileListInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    path: str = Field(..., description="要列出的目录路径，必须在允许目录内")
    pattern: Optional[str] = Field(default="*", description="glob 过滤模式，如 *.py")
    recursive: bool = Field(default=False, description="是否递归子目录")


class FileExistsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    path: str = Field(..., description="要检查的路径")


# ── 工具实现 ──────────────────────────────────────────────────────────────

async def ag_file_read(params: FileReadInput) -> str:
    """
    读取指定路径的文件内容。

    Args:
        params.path: 文件路径（必须在白名单目录内）
        params.encoding: 文件编码（默认 utf-8）

    Returns:
        str: JSON 格式结果，包含 ok/content/size_bytes 或 error
    """
    ok, reason = _is_allowed(params.path)
    if not ok:
        logger.warning("ag_file_read 拒绝: %s", reason)
        return json.dumps({"ok": False, "error": reason})

    p = _normalize(params.path)
    if not p.exists():
        return json.dumps({"ok": False, "error": f"文件不存在：{p}"})
    if not p.is_file():
        return json.dumps({"ok": False, "error": f"路径不是文件：{p}"})

    size = p.stat().st_size
    if size > MAX_FILE_BYTES:
        return json.dumps({
            "ok": False,
            "error": f"文件过大（{size} bytes > {MAX_FILE_BYTES}），请使用其他方式处理"
        })

    try:
        content = p.read_text(encoding=params.encoding, errors="replace")
        logger.info("ag_file_read: %s (%d bytes)", p, size)
        return json.dumps({"ok": True, "path": str(p), "size_bytes": size, "content": content})
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


async def ag_file_write(params: FileWriteInput) -> str:
    """
    写入文本内容到指定路径。

    Args:
        params.path: 目标文件路径（必须在白名单目录内）
        params.content: 写入的文本内容
        params.encoding: 编码（默认 utf-8）
        params.overwrite: 是否覆盖已有文件

    Returns:
        str: JSON 格式结果，包含 ok/path/bytes_written 或 error
    """
    ok, reason = _is_allowed(params.path)
    if not ok:
        logger.warning("ag_file_write 拒绝: %s", reason)
        return json.dumps({"ok": False, "error": reason})

    p = _normalize(params.path)
    if p.exists() and not params.overwrite:
        return json.dumps({"ok": False, "error": f"文件已存在且 overwrite=False：{p}"})

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(params.content, encoding=params.encoding)
        written = p.stat().st_size
        logger.info("ag_file_write: %s (%d bytes)", p, written)
        return json.dumps({"ok": True, "path": str(p), "bytes_written": written})
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


async def ag_file_list(params: FileListInput) -> str:
    """
    列出目录中匹配 pattern 的文件。

    Args:
        params.path: 目录路径
        params.pattern: glob 过滤模式（默认 *）
        params.recursive: 是否递归（默认 False）

    Returns:
        str: JSON 格式 {ok, path, count, entries:[{name,type,size}]}
    """
    ok, reason = _is_allowed(params.path)
    if not ok:
        logger.warning("ag_file_list 拒绝: %s", reason)
        return json.dumps({"ok": False, "error": reason})

    p = _normalize(params.path)
    if not p.exists():
        return json.dumps({"ok": False, "error": f"目录不存在：{p}"})
    if not p.is_dir():
        return json.dumps({"ok": False, "error": f"路径不是目录：{p}"})

    try:
        pattern = params.pattern or "*"
        if params.recursive:
            items = list(p.rglob(pattern))
        else:
            items = list(p.glob(pattern))

        items = items[:MAX_OUTPUT_LINES]
        entries = []
        for item in sorted(items):
            try:
                stat = item.stat()
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "dir" if item.is_dir() else "file",
                    "size_bytes": stat.st_size if item.is_file() else None,
                })
            except Exception:
                pass

        logger.info("ag_file_list: %s pattern=%s count=%d", p, pattern, len(entries))
        return json.dumps({"ok": True, "path": str(p), "pattern": pattern, "count": len(entries), "entries": entries})
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


async def ag_file_exists(params: FileExistsInput) -> str:
    """
    检查路径是否存在。

    Args:
        params.path: 要检查的路径

    Returns:
        str: JSON {ok, path, exists, type: file|dir|none}
    """
    ok, reason = _is_allowed(params.path)
    if not ok:
        return json.dumps({"ok": False, "error": reason})

    p = _normalize(params.path)
    if p.exists():
        ftype = "dir" if p.is_dir() else "file"
        return json.dumps({"ok": True, "path": str(p), "exists": True, "type": ftype})
    return json.dumps({"ok": True, "path": str(p), "exists": False, "type": "none"})
