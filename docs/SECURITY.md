# AntGravity MCP Server - Security Policy

## Path Restrictions

允许访问路径：
- `D:\Obsidian\sync\task\`
- `D:\dev\`
- `D:\AndroidProjects\`

禁止访问路径：
- `C:\Users\keche\.hermes\.env`
- `C:\ProgramData\ssh\`
- `C:\Windows\`

## PowerShell 命令黑名单

以下命令模式被拒绝执行：
- `Remove-Item -Recurse C:\`
- `Format-Volume`
- `Stop-Computer`
- `Restart-Computer`
- `bcdedit`
- `reg delete HKLM`
- `net user`

## 日志

所有工具调用记录到：`D:\Obsidian\sync\task\antgravity-mcp-server\logs\server.log`

## 运行权限

服务以非管理员权限运行。
