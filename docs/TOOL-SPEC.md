# AntGravity MCP Server — 工具说明书

> **服务地址**：`http://192.168.0.124:9000/mcp`
> **协议**：MCP StreamableHTTP（`transport: streamable-http`）
> **工具数量**：**6 个**（Phase 1）

---

## 工具总览

| # | 工具名 | 类型 | 功能 |
|---|--------|------|------|
| 1 | `ag_health_check` | 只读 | 返回 Windows 开发环境状态 |
| 2 | `ag_file_read` | 只读 | 读取 Windows 文件内容 |
| 3 | `ag_file_write` | 写入 | 写入/创建 Windows 文件 |
| 4 | `ag_file_list` | 只读 | 列出目录中的文件 |
| 5 | `ag_file_exists` | 只读 | 检查路径是否存在 |
| 6 | `ag_powershell` | 执行 | 在 Windows 上执行 PowerShell |

---

## 安全约束（全局）

### 文件工具白名单目录
只允许访问以下路径，拒绝其他所有路径：
```
D:\Obsidian\sync\task\    ← 任务文件夹
D:\dev\                   ← 开发项目
D:\AndroidProjects\       ← Android 项目
```

### 黑名单（明确拒绝）
```
C:\Users\keche\.hermes\.env    ← 敏感凭据
C:\ProgramData\ssh\
C:\Windows\
```

### PowerShell 危险命令拦截
```
Remove-Item -Recurse C:\    Format-Volume
Stop-Computer               Restart-Computer
bcdedit                     reg delete HKLM
net user                    rm -rf X:\
```

---

## 工具详情

---

### 1. `ag_health_check`

**功能**：返回 Windows 开发环境的健康状态与软件版本信息。

**参数**：无

**返回示例**：
```json
{
  "ok": true,
  "hostname": "DESKTOP-XXX",
  "user": "keche",
  "cwd": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server",
  "platform": "Windows-11-...",
  "python": "3.12.0",
  "java": "openjdk version \"17.0.x\"",
  "git": "git version 2.43.0.windows.1",
  "android_sdk": true,
  "android_sdk_path": "C:\\Android\\Sdk",
  "antgravity_exe": true
}
```

---

### 2. `ag_file_read`

**功能**：读取 Windows 文件内容（限白名单目录，最大 512KB）。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `path` | str | ✅ | — | 文件路径（需在白名单内） |
| `encoding` | str | ❌ | `utf-8` | 文件编码 |

**返回示例**：
```json
{
  "ok": true,
  "path": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server\\server.py",
  "size_bytes": 12060,
  "content": "#!/usr/bin/env python3\n..."
}
```

---

### 3. `ag_file_write`

**功能**：将文本内容写入 Windows 文件（自动创建父目录）。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `path` | str | ✅ | — | 目标路径（需在白名单内） |
| `content` | str | ✅ | — | 要写入的文本内容 |
| `encoding` | str | ❌ | `utf-8` | 文件编码 |
| `overwrite` | bool | ❌ | `true` | 是否覆盖已有文件 |

**返回示例**：
```json
{
  "ok": true,
  "path": "D:\\Obsidian\\sync\\task\\test.txt",
  "bytes_written": 42
}
```

---

### 4. `ag_file_list`

**功能**：列出目录中的文件和子目录，支持 glob 过滤，最多返回 500 条。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `path` | str | ✅ | — | 目录路径（需在白名单内） |
| `pattern` | str | ❌ | `*` | glob 过滤模式，如 `*.py`, `*.md` |
| `recursive` | bool | ❌ | `false` | 是否递归子目录 |

**返回示例**：
```json
{
  "ok": true,
  "path": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server",
  "pattern": "*.py",
  "count": 3,
  "entries": [
    {"name": "server.py", "path": "D:\\...\\server.py", "type": "file", "size_bytes": 12060},
    {"name": "tools", "path": "D:\\...\\tools", "type": "dir", "size_bytes": null}
  ]
}
```

---

### 5. `ag_file_exists`

**功能**：检查路径是否存在，并返回类型（file / dir / none）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `path` | str | ✅ | 要检查的路径 |

**返回示例**：
```json
{"ok": true, "path": "D:\\dev\\myproject", "exists": true, "type": "dir"}
{"ok": true, "path": "D:\\dev\\notexist", "exists": false, "type": "none"}
```

---

### 6. `ag_powershell`

**功能**：在 Windows 上以非管理员权限执行 PowerShell 命令。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `command` | str | ✅ | — | PowerShell 命令（最大 8192 字符） |
| `timeout` | int | ❌ | `120` | 超时秒数（1-600） |
| `cwd` | str | ❌ | 项目目录 | 工作目录 |

**返回示例**：
```json
{
  "ok": true,
  "exit_code": 0,
  "stdout": "Hello from Windows!\n",
  "stderr": "",
  "timed_out": false
}
```

---

## 如何让 Hermes 测试

### 前置条件
1. AntGravity MCP Server 正在运行（`python server.py` 或开机自启）
2. Hermes 容器已重启加载新 config（`antgravity-mcp` 条目已写入 config.yaml）

### 步骤一：重启 Hermes 加载配置

```bash
docker restart hermes
```

### 步骤二：让 Hermes 直接调用工具

在 Hermes 对话中，直接用自然语言指令：

```
# 测试 1：健康检查
调用 ag_health_check 工具，告诉我 Windows 环境状态

# 测试 2：列出文件
用 ag_file_list 列出 D:\Obsidian\sync\task\antgravity-mcp-server 目录下的 .py 文件

# 测试 3：读取文件
用 ag_file_read 读取 D:\Obsidian\sync\task\antgravity-mcp-server\STATUS.md

# 测试 4：执行 PowerShell
用 ag_powershell 执行：Get-Date; $env:USERNAME; python --version

# 测试 5：写文件
用 ag_file_write 在 D:\Obsidian\sync\task\hermes-test.txt 写入内容 "Hello from Hermes!"
```

### 步骤三：验证 MCP 已连接

在 Hermes 中运行：
```
/mcp
```
应该看到 `antgravity-mcp` 出现在已连接的 MCP server 列表中，并列出 6 个工具。

---

## Phase 2 计划工具（未实现）

| 工具名 | 功能 |
|--------|------|
| `ag_git_status` | 查看 Git 仓库状态 |
| `ag_git_commit` | 提交并推送 |
| `ag_run_gradle` | 执行 Gradle 构建 |
| `ag_android_build_apk` | 构建 Android APK |
| `ag_cdp_eval` | Chrome DevTools 远程执行 JS |
