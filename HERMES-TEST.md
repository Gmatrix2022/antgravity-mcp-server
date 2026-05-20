# AntGravity MCP Server — Hermes 测试指令

> 本文件路径（容器内）：`/sync/task/antgravity-mcp-server/HERMES-TEST.md`
> MCP Server：`http://192.168.0.124:9000`

请按以下步骤逐一测试，每步完成后报告结果。

---

## Step 0：确认 MCP 已连接

运行 `/mcp` 命令，确认 `antgravity-mcp` 出现在列表中，且列出 6 个工具：
- ag_health_check
- ag_file_read
- ag_file_write
- ag_file_list
- ag_file_exists
- ag_powershell

---

## Step 1：健康检查

调用工具 `ag_health_check`，无需参数。

预期结果：返回包含 `ok: true`、hostname、python 版本、git 版本等信息的 JSON。

---

## Step 2：列出目录文件

调用工具 `ag_file_list`，参数：
```json
{
  "path": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server",
  "pattern": "*.py",
  "recursive": false
}
```

预期结果：列出 `server.py` 及 `tools/` 下的 `.py` 文件。

---

## Step 3：读取文件

调用工具 `ag_file_read`，参数：
```json
{
  "path": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server\\STATUS.md"
}
```

预期结果：返回 STATUS.md 的完整内容。

---

## Step 4：写入文件

调用工具 `ag_file_write`，参数：
```json
{
  "path": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server\\hermes-write-test.txt",
  "content": "Hermes wrote this at {当前时间}. MCP write test passed ✅"
}
```

预期结果：`{"ok": true, "bytes_written": ...}`

---

## Step 5：检查文件存在

调用工具 `ag_file_exists`，参数：
```json
{
  "path": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server\\hermes-write-test.txt"
}
```

预期结果：`{"exists": true, "type": "file"}`

---

## Step 6：执行 PowerShell

调用工具 `ag_powershell`，参数：
```json
{
  "command": "Write-Host 'Hello from Hermes!'; Get-Date; $env:USERNAME; python --version"
}
```

预期结果：返回包含当前时间、用户名、Python 版本的输出，`exit_code: 0`。

---

## 测试完成后

汇报每个步骤的结果（pass/fail），并将汇总写入：
`D:\Obsidian\sync\task\antgravity-mcp-server\hermes-test-report.md`
