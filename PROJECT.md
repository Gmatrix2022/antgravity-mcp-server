# AntGravity MCP Server 建设任务

> 状态：planned  
> 生成时间：2026-05-16  
> 目标执行者：AntGravity / Windows 侧开发智能体  
> 任务路径：`D:\Obsidian\sync\task\antgravity-mcp-server\`

---

## 1. 目标

在 Windows 物理机上建设一个 **AntGravity 专用 MCP Server**，让 Hermes 容器可以通过 HTTP/StreamableHTTP MCP 协议调用 AntGravity / Windows 开发环境能力。

最终效果：

```text
Hermes 容器
  ↓ MCP HTTP
AntGravity MCP Server（Windows）
  ├─ 调用 AntGravity/CDP 能力
  ├─ 执行 PowerShell
  ├─ 管理工作区文件
  ├─ 执行 Git/Gradle/Node 构建
  └─ 为 Android / PPT / 文档 / 代码任务提供标准工具接口
```

这不是普通 Windows MCP。普通 Windows MCP 是桌面/文件/鼠标键盘层。这个项目要做的是 **AntGravity 专用智能体协作层**。

---

## 2. 背景

当前 Hermes ↔ AntGravity 已有 Phase 1 文件队列方案：

```text
Hermes 写 JSON → inbox/
AntGravity watcher 读取 → 执行
AntGravity 写结果 → outbox/
Hermes 读取结果
```

路径：

```text
D:\Obsidian\sync\task\hermes-antigravity-collaboration\
```

这个方案可用，但不是标准协议，扩展性有限。

下一步改为：

```text
Hermes 作为 MCP Client
AntGravity-MCP-Server 作为 MCP Server
通过 HTTP/StreamableHTTP 跨主机调用
```

---

## 3. 非目标

本任务 **不做**：

1. 不修改 Hermes 主网关配置。
2. 不重启 Hermes gateway。
3. 不接管所有 Windows 桌面操作。
4. 不做完整 IDE 替代品。
5. 不强依赖 Android Studio 图形界面。
6. 不暴露全盘危险操作；所有工具要限制路径和命令范围。

---

## 4. 技术选型

### 4.1 服务端语言

优先 Python。

推荐依赖：

```powershell
pip install "mcp[cli]" fastapi uvicorn pydantic httpx websockets
```

如果 Python MCP SDK 在 Windows 上不好用，可退回 Node.js TypeScript 实现，但第一版优先 Python。

### 4.2 传输协议

必须支持 Hermes 当前可用的 HTTP / StreamableHTTP MCP。

推荐监听：

```text
http://0.0.0.0:8901/mcp
```

不要只监听 `127.0.0.1`，容器访问不到。

### 4.3 Windows 防火墙

必须添加防火墙规则：

```powershell
New-NetFirewallRule -DisplayName "AntGravity MCP 8901" -Direction Inbound -Protocol TCP -LocalPort 8901 -Action Allow
```

---

## 5. 目录结构

在 Windows 上创建：

```text
D:\Obsidian\sync\task\antgravity-mcp-server\
├── PROJECT.md
├── STATUS.md
├── README.md
├── requirements.txt
├── server.py
├── tools\
│   ├── __init__.py
│   ├── powershell_tools.py
│   ├── filesystem_tools.py
│   ├── git_tools.py
│   ├── build_tools.py
│   ├── android_tools.py
│   └── antgravity_cdp_tools.py
├── scripts\
│   ├── start-server.ps1
│   ├── install-deps.ps1
│   ├── check-health.ps1
│   └── open-firewall.ps1
└── docs\
    ├── TOOL-SPEC.md
    ├── SECURITY.md
    └── TEST-REPORT.md
```

---

## 6. 第一版工具清单

### 6.1 健康检查

#### `ag_health_check`

返回：

```json
{
  "ok": true,
  "hostname": "...",
  "user": "...",
  "cwd": "...",
  "antgravity_cdp": true,
  "java": "17.x",
  "git": "2.x",
  "android_sdk": true
}
```

---

### 6.2 文件工具

路径必须限制在：

```text
D:\Obsidian\sync\task\
D:\dev\
D:\AndroidProjects\
```

工具：

- `ag_file_read(path)`
- `ag_file_write(path, content)`
- `ag_file_list(path, pattern)`
- `ag_file_exists(path)`

禁止访问：

```text
C:\Users\keche\.hermes\.env
C:\ProgramData\ssh\
C:\Windows\
```

---

### 6.3 PowerShell 工具

#### `ag_powershell(command, timeout=120)`

要求：

1. 默认非管理员。
2. 超时必须生效。
3. 返回 stdout/stderr/exit_code。
4. 默认工作目录限制在任务目录。
5. 高危命令拒绝执行。

拒绝关键词：

```text
Remove-Item -Recurse C:\
Format-Volume
Stop-Computer
Restart-Computer
bcdedit
reg delete HKLM
net user
```

---

### 6.4 Git 工具

- `ag_git_clone(repo_url, target_dir, branch?)`
- `ag_git_status(repo_dir)`
- `ag_git_apply_patch(repo_dir, patch_text)`
- `ag_git_commit(repo_dir, message)`

---

### 6.5 构建工具

- `ag_run_gradle(project_dir, task, timeout=1800)`
- `ag_run_npm(project_dir, script, timeout=1800)`
- `ag_run_python(project_dir, args, timeout=600)`

返回必须包含：

```json
{
  "exit_code": 0,
  "stdout_tail": "最后200行",
  "stderr_tail": "最后200行",
  "artifacts": ["生成文件路径"]
}
```

---

### 6.6 Android 工具

用于后续 fcitx5-android + Whisper 语音输入开发。

工具：

- `ag_android_check_env()`
- `ag_android_install_cmdline_tools()`
- `ag_android_install_sdk(packages)`
- `ag_android_build_apk(project_dir, variant)`
- `ag_android_find_apks(project_dir)`

默认安装：

```text
platform-tools
platforms;android-35
build-tools;35.0.0
ndk;27.0.12077973
cmake;3.22.1
```

---

### 6.7 AntGravity / CDP 工具

AntGravity 已知路径：

```text
C:\Users\keche\AppData\Local\Programs\Antigravity\Antigravity.exe
```

已知 CDP 端口：

```text
http://localhost:9000/json
ws://localhost:9000
```

工具：

- `ag_cdp_status()`：检查 9000 是否可访问
- `ag_cdp_list_pages()`：列出页面
- `ag_cdp_eval(page_id, expression)`：执行 JS
- `ag_launch_antgravity_cdp()`：启动带 `--remote-debugging-port=9000` 的 AntGravity

第一版可以只做 CDP 状态检查和页面列表，不强行自动操作 UI。

---

## 7. Hermes 侧预期配置

注意：本任务只生成配置建议，不直接修改 `/opt/data/config.yaml`。

预期后续由 Hermes 按配置修改安全流程添加：

```yaml
mcp_servers:
  antgravity:
    url: "http://192.168.0.124:8901/mcp"
    timeout: 180
    connect_timeout: 30
```

如果 Windows IP 变动，使用实际局域网 IP 替换。

---

## 8. 验收标准

### 8.1 Windows 本机验证

```powershell
curl http://localhost:8901/health
```

必须返回：

```json
{"ok": true}
```

### 8.2 容器内验证

Hermes 容器内执行：

```bash
curl -s http://192.168.0.124:8901/health
```

必须能访问。

### 8.3 MCP 工具发现

Hermes 添加 MCP 配置并重启后，应出现工具名前缀：

```text
mcp_antgravity_ag_health_check
mcp_antgravity_ag_powershell
mcp_antgravity_ag_file_read
mcp_antgravity_ag_android_build_apk
```

### 8.4 Android 构建验证

用一个最小 Gradle Android 项目验证：

```text
ag_android_check_env → ok
ag_android_build_apk → 生成 apk 路径
```

---

## 9. 实施阶段

### Phase 0：只做 HTTP health

目标：先打通跨主机网络。

交付：

- `server.py`
- `/health` endpoint
- `start-server.ps1`
- 防火墙规则脚本

### Phase 1：MCP 基础工具

目标：Hermes 能发现并调用 MCP 工具。

交付：

- `ag_health_check`
- `ag_file_read/write/list`
- `ag_powershell`

### Phase 2：构建工具

目标：支持真实开发任务。

交付：

- Git clone/status/patch
- Gradle/npm/python build
- artifact 收集

### Phase 2.5：浏览器控制工具（Browser Control via Playwright + CDP）

**更新时间：2026-05-18**

#### 背景与目标

Hermes（容器侧 Agent）需要能控制 Windows 上的浏览器，完成：
- 自动化网页操作（填表、点击、导航）
- 截图 + 内容提取（辅助 Hermes 理解页面）
- 执行 JavaScript（操作 DOM、抓取数据）

#### 架构选型

```text
Hermes 容器
  ↓ MCP 工具调用（HTTP, port 9000）
AntGravity MCP Server（Windows :9000）
  ↓ Playwright Python API（本地调用）
Chrome / Edge（Windows，CDP port :9222）
  └── WebView2（Windows 内置 Edge 引擎）
```

**选型决策**：

| 方案 | 描述 | 决策 |
|------|------|------|
| 路径 A | 控制 AntGravity.exe 内嵌 WebView2（需改 Tauri 源码暴露 CDP 端口） | ❌ 暂缓，需修改客户端 |
| **路径 B** | **MCP Server 用 Playwright 管理独立 Chrome/Edge 实例** | ✅ 当前实施 |

路径 B 优点：
- 现在即可实现，不依赖 AntGravity.exe 改动
- Windows 已内置 Edge/WebView2，Playwright 直接驱动
- 浏览器实例生命周期由 MCP Server 管理，Hermes 随时调用

#### 依赖

```powershell
pip install playwright
playwright install chromium   # 或 msedge（已内置 Windows）
```

#### 新增工具：ag_browser_*

| 工具名 | 功能 | 关键参数 |
|--------|------|----------|
| `ag_browser_open` | 打开 URL，返回 page_id | `url`, `wait_until`(load/networkidle) |
| `ag_browser_screenshot` | 截图 → base64 PNG | `page_id`, `full_page` |
| `ag_browser_get_text` | 提取页面正文（去除标签）| `page_id`, `selector`(可选) |
| `ag_browser_get_html` | 获取 HTML 源码（限 200KB）| `page_id`, `selector`(可选) |
| `ag_browser_eval` | 执行 JavaScript，返回结果 | `page_id`, `expression` |
| `ag_browser_click` | 点击元素（CSS selector）| `page_id`, `selector`, `timeout` |
| `ag_browser_fill` | 填写表单字段 | `page_id`, `selector`, `value` |
| `ag_browser_wait` | 等待元素出现/消失 | `page_id`, `selector`, `state` |
| `ag_browser_close` | 关闭页面或整个浏览器 | `page_id`(可选，不传则关全部) |
| `ag_browser_list_pages` | 列出所有打开的页面 | — |

#### 工具接口设计

```python
# 打开页面，返回 page_id 用于后续操作
ag_browser_open(
    url: str,                           # 必填
    wait_until: str = "load",           # load / networkidle / domcontentloaded
    timeout: int = 30,                  # 秒
) -> {"ok": bool, "page_id": str, "title": str, "url": str}

# 截图（Hermes 可存入文件再分析）
ag_browser_screenshot(
    page_id: str,                       # 必填
    full_page: bool = False,            # True = 整页截图
    save_path: str | None = None,       # 可选，保存到 Windows 路径
) -> {"ok": bool, "base64": str, "width": int, "height": int, "saved_to": str | None}

# 执行 JS
ag_browser_eval(
    page_id: str,
    expression: str,                    # JS 表达式，返回值必须可序列化
    timeout: int = 10,
) -> {"ok": bool, "result": any, "error": str | None}

# 点击
ag_browser_click(
    page_id: str,
    selector: str,                      # CSS selector
    timeout: int = 10,
) -> {"ok": bool, "error": str | None}

# 填表
ag_browser_fill(
    page_id: str,
    selector: str,
    value: str,
    timeout: int = 10,
) -> {"ok": bool, "error": str | None}

# 列出所有页面
ag_browser_list_pages() -> {
    "ok": bool,
    "pages": [{"page_id": str, "title": str, "url": str}]
}
```

#### 安全约束

1. **URL 黑名单**：拒绝 `file:///C:/Windows/`、`file:///C:/Users/keche/.hermes/` 等本地敏感路径
2. **JS 执行**：不允许 `fetch("file://...")` 读本地文件；超时强制终止
3. **截图大小**：base64 输出限制 2MB，超出自动压缩或返回错误
4. **并发页面**：最多同时开 5 个页面，超出拒绝 `ag_browser_open`
5. **浏览器实例**：MCP Server 启动时懒初始化，关闭时自动清理

#### 状态管理

```python
# tools/browser_tools.py 内部维护
_browser: Browser | None = None        # Playwright browser 实例（懒初始化）
_pages: dict[str, Page] = {}           # page_id → Page 对象
MAX_PAGES = 5
```

#### 文件结构变更

```text
tools/
  browser_tools.py    ← 新增（ag_browser_* 全部工具）
```

#### Phase 2.5 实施顺序

1. `pip install playwright && playwright install chromium`
2. 实现 `browser_tools.py`（ag_browser_open + screenshot + get_text + eval）
3. 在 `server.py` 注册工具
4. 本地测试：`ag_browser_open("https://httpbin.org/get")` → 截图验证
5. Hermes 端测试：调用工具，截图 base64 存为文件后 `ag_file_read` 取回
6. 路径 A（AntGravity.exe WebView2 直连）：等 Tauri 侧加 `--remote-debugging-port` 后再接入

### Phase 3：Android 工具链

目标：支持 fcitx5-android 构建。

交付：

- JDK 17 检测/安装指引
- Android SDK/NDK/CMake 安装
- APK 构建

### Phase 4：AntGravity CDP 桥接

目标：探索 AntGravity 自身能力。

交付：

- 启动 AntGravity CDP
- 列页面
- 执行基础 JS
- 写明能力边界

---

## 10. 安全要求

1. 不允许默认管理员权限运行。
2. 不允许全盘文件读写。
3. 不允许暴露 `.env`、SSH key、浏览器密码库。
4. PowerShell 命令必须有黑名单过滤。
5. 所有工具调用写日志：

```text
D:\Obsidian\sync\task\antgravity-mcp-server\logs\server.log
```

6. 每个工具结果限制输出长度，避免把超长日志塞回 Hermes。

---

## 11. 给 AntGravity 的执行提示

你是 Windows 侧开发智能体。请按本文档在：

```text
D:\Obsidian\sync\task\antgravity-mcp-server\
```

创建项目并完成 Phase 0 → Phase 1。

优先级：

1. 先让 `/health` 可从 Hermes 容器访问。
2. 再让 MCP 工具可被 Hermes 发现。
3. 再实现文件、PowerShell、Git、Gradle、Android 工具。
4. 不要先碰 Hermes 主配置。
5. 不要重启 Hermes gateway。

完成后写：

```text
D:\Obsidian\sync\task\antgravity-mcp-server\docs\TEST-REPORT.md
```

内容包括：

- 服务启动命令
- 监听端口
- 防火墙规则状态
- 本机 curl 测试结果
- 容器 curl 测试结果
- 已实现工具列表
- 未完成/阻塞项

---

## 12. 后续 Android 输入法任务接入

AntGravity-MCP Server 建好后，下一步任务才是：

```text
Fork fcitx5-android
加入语音按钮
录音上传 Hermes/N6M 本地 Whisper
返回文字后注入输入框
构建 APK
```

届时 Hermes 通过 MCP 调用：

```text
ag_git_clone
ag_android_check_env
ag_git_apply_patch
ag_android_build_apk
ag_android_find_apks
```

这样以后就不用再通过 inbox/outbox 文件队列派发复杂开发任务。

---

## 13. Phase 5：远程观察与共享黑板（2026-05-18 追加）

为支持 `antigravity-bridge-service` + `antigravity-android-client` 两个新项目（远程观察 AntGravity 桌面 Agent 实时状态），并让 AntGravity 加入共享看板黑板，本 MCP server 需追加以下工具组。

### 13.1 设计原则

- **AntGravity 边干边写**：每步推理/工具调用前调 `record_step`，落盘到工作目录的 `.hermes-stream/`
- **打断工作流可接受**：用户已确认这是合理代价，不追求 zero-overhead
- **看板做共享黑板**：AntGravity、Hermes、其他 agent 都能读写 `/sync/kanban.db`（Windows 等价 `D:\Obsidian\sync\kanban.db`）
- **按需查询，不主动推送**：Hermes 容器要看 AntGravity 状态时调 `get_current_status`，不需要常驻 watcher

### 13.2 新增工具：record_step

签名：

```python
ag_record_step(
    type: Literal["thought", "tool_call", "tool_result", "pending_approve", "done", "error"],
    content: str,
    step_id: str | None = None,        # 不传则自增
    workdir: str | None = None,        # 不传则用当前工作目录
    meta: dict | None = None,           # task_id / tool_name 等
) -> dict
```

行为：

1. 如果 `<workdir>/.hermes-stream/` 不存在，自动创建
2. 写入文件：`<workdir>/.hermes-stream/steps/<timestamp>-<step_id>-<type>.json`
3. 同时更新 `<workdir>/.hermes-stream/current.json`（最新状态，方便快速查询）
4. 返回 `{ok: true, file: "...", step_id: "..."}`

派发任务的 prompt 模板里要强约束：

> 每完成一步推理/工具调用前，必须先调 `ag_record_step` 记录，再继续。违反约束视为执行失败。

### 13.3 新增工具：get_current_status

签名：

```python
ag_get_current_status(workdir: str) -> dict
```

行为：

1. 读 `<workdir>/.hermes-stream/current.json`
2. 返回当前 step 类型、内容、时间、是否在等 approve
3. 如果文件不存在返回 `{status: "no_active_task"}`

用途：飞书/钉钉里你问"AntGravity 现在干到哪了"，Hermes agent 调这个工具就能拿到最新状态，无需常驻监听。

### 13.4 新增工具：get_step_history

签名：

```python
ag_get_step_history(workdir: str, limit: int = 50, since_ts: int | None = None) -> dict
```

行为：

1. 列 `<workdir>/.hermes-stream/steps/` 下文件
2. 按时间倒序，最近 `limit` 步
3. 可选时间过滤
4. 返回 `[{type, content, timestamp, step_id, meta}, ...]`

用途：补做历史归档、客户端断网后追赶。

### 13.5 新增工具：accept_action

签名：

```python
ag_accept_action(
    workdir: str,
    action: Literal["approve", "reject", "run", "accept_all"],
    step_id: str,
    comment: str | None = None,
) -> dict
```

行为：

1. 写入 `<workdir>/.hermes-stream/actions/<timestamp>-<action>.json`
2. AntGravity Agent 在 prompt 里被指示循环检查这个目录
3. 看到对应 `step_id` 的 action 就响应（继续/中止/重做）

用途：手机 APP 点 approve/reject 时，Bridge Service 反向调用本工具，把意图落到磁盘，AntGravity 看到后响应。

### 13.6 新增工具组：kanban_*

让 AntGravity 直接读写共享看板。Windows 路径：`D:\Obsidian\sync\kanban.db`（即 `/sync/kanban.db`）

```python
ag_kanban_create(title: str, body: str, assignee: str = "antgravity",
                 parents: list[str] = [], priority: int = 0) -> dict
ag_kanban_update(task_id: str, status: str | None = None,
                 result: str | None = None) -> dict
ag_kanban_comment(task_id: str, body: str, author: str = "antgravity") -> dict
ag_kanban_complete(task_id: str, summary: str, metadata: dict = {}) -> dict
ag_kanban_list(assignee: str | None = None, status: str | None = None) -> dict
ag_kanban_get(task_id: str) -> dict
```

实现要点：

- 直接 `sqlite3` 操作（schema 见 `/opt/data/skills/devops/kanban-orchestrator/references/kanban-schema.md`）
- 写操作要带事务
- 多 agent 并发用 `BEGIN IMMEDIATE` 防冲突

### 13.7 .hermes-stream 目录约定

```text
<workdir>/.hermes-stream/
├── current.json                # 最新状态（覆盖写）
├── steps/
│   └── <ts>-<step_id>-<type>.json
├── actions/                    # 反向意图（手机端写入）
│   └── <ts>-<action>.json
└── tree.json                   # 工作目录文件树（每分钟刷新）
```

`current.json` schema：

```json
{
  "task_id": "...",
  "step_id": "042",
  "type": "pending_approve",
  "content": "建议运行 npm install，是否同意？",
  "timestamp": 1716000000,
  "meta": { "tool_name": "run_command" },
  "is_pending": true
}
```

### 13.8 Phase 5 实施步骤

1. **先修 421**（最高优先级，看板 `795fa434`）：`TrustedHostMiddleware allowed_hosts=["*"]`
2. 加 `ag_record_step` 工具（最小可用版）
3. 加 `ag_get_current_status` 工具
4. 加 `ag_get_step_history` 工具
5. 加 `ag_accept_action` 工具
6. 加 `ag_kanban_*` 工具组
7. 全部完成后通知，Hermes 这边更新派发 prompt 模板

> **注意**：`ag_notify_status` 已删除——不需要。AntGravity 直接调 Hermes 的 `send_message` MCP 推飞书即可（Hermes 已是 MCP server，见 `hermes_tools_mcp_server.py`）。

### 13.9 关联项目

| 项目 | 关系 |
|---|---|
| `antigravity-bridge-service` | 下游：消费 .hermes-stream/ 推给手机 |
| `antigravity-android-client` | 终端用户：触发 ag_accept_action |
| `hermes-antigravity-collaboration` | 派发 prompt 模板要加 record_step 强约束 |

