# AntGravity MCP Server — 工作日志

---

## 2026-05-17（今日进展）

### ✅ 已完成

**端口问题彻底解决**
- 8901 → 在 `8899-8998` 保留范围内，失败
- 8790 → 在 `8743-8842` 保留范围内，失败
- **9000** → 安全，不在任何 Windows Hyper-V/WSL 保留范围内，成功 ✅

**Phase 0 验收通过**
```
GET http://localhost:9000/health → 200 OK
{"ok":true,"service":"antgravity-mcp","version":"0.1.0","port":9000}
```

**防火墙规则**
```
Rule: "AntGravity MCP 9000"
Direction: Inbound | Action: Allow | Protocol: TCP | Port: 9000 | Enabled: True
```

**Phase 1 跨主机验证通过**
```
docker exec hermes curl http://192.168.0.124:9000/health
→ {"ok":true,"service":"antgravity-mcp","version":"0.1.0","port":9000}
```

### 🔧 进行中（明天继续）

**问题：MCP `/mcp` 端点 500 错误**

根因已定位：
```
RuntimeError: Task group is not initialized. Make sure to use run().
```

`FastMCP.streamable_http_app()` 返回的 Starlette 实例携带必要的 lifespan（`session_manager.run()` 初始化 task group）。  
把它 `app.mount("/", mcp_app)` 到外部 FastAPI 时，**lifespan 不会被触发**，导致 task group 未初始化。

**已应用的修复方案（待验证）**
- 不再使用外部 FastAPI
- 直接以 `mcp.streamable_http_app()` 返回的 Starlette 为主 app
- 在其 `routes` 列表头部 `insert(0, Route("/health", ...))` 注入健康检查路由
- 代码已写入 `server.py`，**尚未重启验证**

### 📋 明天第一件事

```bash
cd D:\Obsidian\sync\task\antgravity-mcp-server
python server.py
```

然后验证：
```powershell
# 1. /health 仍然 OK
Invoke-WebRequest -Uri "http://localhost:9000/health" -UseBasicParsing

# 2. /mcp 不再 500
$body = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
Invoke-WebRequest -Uri "http://localhost:9000/mcp" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing

# 3. Hermes 容器跨主机验证 /mcp
docker exec hermes curl -X POST http://192.168.0.124:9000/mcp -H "Content-Type: application/json" -d '...'
```

如果 `/mcp` 通了，后续：
- [x] 在 Hermes config 注册 `antgravity_mcp`（写入 `~/.hermes/config.yaml`）
- [x] 设置 server 开机自启（Task Scheduler / NSSM）
- [x] 测试 `ag_health_check`、`ag_file_read`、`ag_powershell` 工具调用

---

## 2026-05-20（今日进展）

### ✅ 已完成
1. **彻底解决 Windows 服务启动异常**：
   - 之前 NSSM 托管的 `AntGravityMCP` 系统服务处于 `Paused` 状态。
   - 检查 `logs/service.log` 发现主应用使用 PyManager `python.exe` 在 `LocalSystem` 账户下运行，导致 `sys.path` 缺失用户本地安装的 site-packages，报错 `ModuleNotFoundError: No module named 'uvicorn'`。
   - 通过管理员提权将服务的 `Application` 配置直接修改为用户的本地 Python 主程序（`C:\Users\keche\AppData\Local\Python\pythoncore-3.14-64\python.exe`）。
   - 重新启动服务成功，状态恢复为 **Running**。
2. **状态与健康验证**：
   - 确认 `9000` 端口正处于 Listen 状态。
   - `http://localhost:9000/health` 验证通过，成功返回 200 OK。
3. **Hermes 迁移同步与防劫持绕过**：
   - 已获知 Hermes 客户端容器已迁移至局域网内独立的 Ubuntu 宿主机（IP：`192.168.0.126`）。
   - 已通过设置 `enable_dns_rebinding_protection=False` 与加载 `TrustedHostMiddleware`，成功解决了跨主机 Host 头解析引发的 `421` 问题，打通双向长连接。
4. **windows-mcp 27 个工具全整合**：
   - 修改 `server.py`，无缝接入 `windows-mcp` 后台 Watchdog 焦点监听的 lifespan 生命周期。
   - 注册 18 个富桌面 GUI 控制交互工具，同原本的 9 个 `ag_*` 工具组合成 27 个全功能控制工具。
5. **自动化 E2E 完整通过 (8/8)**：
   - 运行本地 MCP 端到端测试脚本 `test_mcp.py`，全部 8 大步骤（初始化、握手、列出工具、执行 `ag_health_check`、文件读写检测、PowerShell 验证等）均 **100% 成功通过**。
   - 编写完成全新的 [hermes-test-report.md](file:///d:/Obsidian/sync/task/antgravity-mcp-server/hermes-test-report.md) 并成功留档。

---

## 关键文件

| 文件 | 说明 |
|------|------|
| `server.py` | 主入口，**已集成并完美验证通过** |
| `tools/filesystem_tools.py` | 文件系统工具 |
| `tools/powershell_tools.py` | PowerShell 执行工具 |
| `logs/server.log` | 运行日志 |
| `hermes-test-report.md` | **新 E2E 整合测试报告** |

## Windows 保留端口速查（Hyper-V/WSL 占用）

```
1074-1273, 1174-1273
4549-4648
8260-8989（几乎整段）
9015-9477
9527-9626
12366-12765
50000-50059
```

**9000 安全。**
