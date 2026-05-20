# AntGravity MCP Server — 全量工具使用说明书 (27 工具)

> **服务统一入口**：`http://192.168.0.124:9000/mcp`  
> **协议传输层**：MCP streamable-http (Server-Sent Events 传输模式)  
> **服务承载状态**：已作为 Windows 系统服务 `AntGravityMCP` 托管运行，监听安全端口 `9000`，允许局域网内任意 Host header。  
> **全量工具数量**：**27 个**（整合了 `windows-mcp` 开源库的 18 个核心 OS 交互工具 + 9 个 AntGravity 专属增强与 Office 工具）。

---

## 📂 工具概览与分类

| 类别 | 工具数 | 工具名称 | 核心作用 |
| :--- | :--- | :--- | :--- |
| **桌面 GUI 模拟** | 8 | `Click`, `Type`, `Scroll`, `Move`, `Shortcut`, `MultiSelect`, `MultiEdit`, `Wait` | 物理模拟鼠标点击、移动、滚轮、键盘文本输入、多选、批量编辑与组合快捷键 |
| **视觉与网页感知** | 3 | `Screenshot`, `Snapshot`, `Scrape` | 高速截图、抓取屏幕 UI 树结构（包含坐标与可见文本）、爬取网页内容 |
| **Windows 系统服务** | 5 | `App`, `Process`, `Clipboard`, `Notification`, `Registry` | 管理应用窗口与进程、读写系统剪贴板与注册表、推送 Toast 弹窗通知 |
| **沙箱文件系统** | 4 | `ag_file_list`, `ag_file_read`, `ag_file_write`, `ag_file_exists` | 安全受控的文件列出、读取、写入与存在性探测（附带沙箱白名单） |
| **系统底层执行** | 1 | `ag_powershell` | 执行非管理员权限的任意多行 PowerShell 脚本，支持 adb, git, gradle 等开发工具 |
| **Office PPTX 自动化** | 3 | `ag_pptx_read_slide`, `ag_pptx_fill_text`, `ag_pptx_create_slide` | 远程直接读写、新建和填充当前活动 PowerPoint 幻灯片文本内容 |
| **环境探测** | 1 | `ag_health_check` | 扫描 Windows 机型的 Python/Java/Git/Android SDK 环境完整度 |

---

## 🛠️ 第一类：桌面 GUI 模拟与物理交互 (8 个)

这些工具物理模拟用户的键鼠操作，用于自动化控制任意第三方 Windows 客户端软件（如 IDE、浏览器、微信、PowerPoint 等）。

### 1. `Click`
* **功能**：模拟鼠标在指定位置的点击，或根据文字模糊匹配自动寻找 UI 元素并点击。
* **参数**：
  * `loc` (list): 二维坐标 `[x, y]`。例如：`[100, 250]`。
  * `label` (str/int): 要点击的 UI 元素名称（可配合 `Snapshot` 读出的元素名称）或元素 ID。
  * `button` (str): 鼠标按键（`"left"`（默认）, `"right"`, `"middle"`）。
  * `clicks` (int): 点击次数，`1` 为单键，`2` 为双击。

### 2. `Type`
* **功能**：在当前焦点处打字输入文本，或在指定坐标/UI 元素输入。
* **参数**：
  * `text` (str, 必填)：要输入的内容。
  * `loc` (list, 可选)：定位的二维坐标 `[x, y]`。
  * `label` (str/int, 可选)：定位的 UI 元素名称或 ID。
  * `clear` (bool, 可选)：输入前是否清空文本框（默认为 False）。
  * `press_enter` (bool, 可选)：输入完成后是否模拟敲击回车。

### 3. `Scroll`
* **功能**：模拟滚轮在特定位置或当前鼠标位置的滚动。
* **参数**：
  * `loc`/`label` (可选)：滚动发生的坐标或 UI 元素。
  * `type` (str)：滚动方向（`"vertical"`（默认）或 `"horizontal"`）。
  * `direction` (str)：滚动朝向（`"down"`（默认）或 `"up"`）。
  * `wheel_times` (int)：滚动格数（默认 `1`）。

### 4. `Move`
* **功能**：移动鼠标指针至指定坐标，或执行拖拽（Drag & Drop）操作。
* **参数**：
  * `loc`/`label`：目标坐标或 UI 元素名称。
  * `drag` (bool)：若为 True，则从当前鼠标位置按住左键拖拽至目标位置。

### 5. `Shortcut`
* **功能**：触发物理键盘快捷键组合，对活动窗口起效。
* **参数**：
  * `shortcut` (str, 必填)：由 `+` 拼接的键名，不区分大小写。例如：`"ctrl+c"`、`"alt+f4"`、`"win+r"`。

### 6. `Wait`
* **功能**：阻塞并暂停执行指定的秒数，以便等待窗口渲染、软件启动或动画完成。
* **参数**：
  * `duration` (int, 必填)：暂停时间（秒）。

### 7. `MultiSelect`
* **功能**：批量多选多个文件或多选框（相当于按住 Ctrl 键依次点击）。
* **参数**：
  * `locs` (list): 坐标二维数组 `[[x1,y1], [x2,y2], ...]`。
  * `labels` (list): UI 元素标识或标签列表。

### 8. `MultiEdit`
* **功能**：批量对多个不同的表单字段进行文本编辑填充。
* **参数**：
  * `locs` (list): 带文本的坐标数组 `[[x1,y1,"text1"], ...]`。
  * `labels` (list): 带文本的标签数组 `[[label1,"text1"], ...]`。

---

## 👁️ 第二类：视觉、屏幕与网络感知 (3 个)

提供屏幕感知，协助 AI 读懂屏幕状态、定位目标文字以及提取网页内容。

### 9. `Screenshot`
* **功能**：高速截取当前 Windows 屏幕并返回原始二进制图像（支持 base64，常用于视觉模型）。
* **参数**：
  * `display` (int, 可选)：多显示器选择（默认为主屏 `0`）。

### 10. `Snapshot`
* **功能**：截取当前屏幕并提取最核心的 UI 布局结构信息，包括包含的所有文字、按钮、文本输入框及其具体的物理像素坐标。
* **参数**：
  * `use_ui_tree` (bool, 可选)：使用 Windows UI Automation 底层树节点检索。
  * `use_vision` (bool, 可选)：结合视觉对屏幕文本做 OCR 识别（默认 True）。

### 11. `Scrape`
* **功能**：爬取指定网页的数据并转成干净的 Markdown text，用于信息检索。
* **参数**：
  * `url` (str, 必填)：目标网页的网址。

---

## 🖥️ 第三类：Windows 系统服务与管理器 (5 个)

提供进程、剪贴板、注册表与系统级弹窗的直接访问控制，避开复杂的 GUI 模拟，速度极快。

### 12. `App`
* **功能**：启动指定路径的应用程序，或者最大化/移至前台已存在的应用程序窗口。
* **参数**
  * `mode` (str)：`"launch"` (默认，启动新进程) 或 `"focus"` (聚焦已有窗口)。
  * `name` (str)：若 launch，为绝对路径（如 `notepad.exe`）；若 focus，为窗口标题。

### 13. `Process`
* **功能**：列出当前运行的所有进程（可按 CPU 或内存占用排序），或按 PID / 名称强行关闭进程。
* **参数**：
  * `mode` (str, 必填)：`"list"` (列出进程) 或 `"kill"` (杀进程)。
  * `name`/`pid` (可选)：杀进程时的定位标志。

### 14. `Clipboard`
* **功能**：获取或写入 Windows 剪贴板文本内容。
* **参数**：
  * `mode` (str, 必填)：`"get"` (获取剪贴板) 或 `"set"` (写入剪贴板)。
  * `text` (str, 可选)：写入时的文本。

### 15. `Notification`
* **功能**：向 Windows 系统右下角通知中心发送一条气泡通知。
* **参数**：
  * `title` (str, 必填)：通知标题。
  * `message` (str, 必填)：通知正文内容。
  * `app_id` (str, 必填)：通知发送者 ID（如 `AntGravity`）。

### 16. `Registry`
* **功能**：直接读写 Windows 系统注册表键值。
* **参数**：
  * `mode` (str, 必填)：`"read"` 或 `"write"`。
  * `path` (str, 必填)：键路径，如 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`。
  * `name`/`value`/`type` (可选)：具体项的名称、值和类型（如 `REG_SZ`）。

---

## 🛡️ 第四类：AntGravity 专属文件与系统增强 (7 个)

针对日常文件开发与底层构建工具链，提供了定制化的安全受控沙箱与高速文件操作。

### 17. `ag_health_check`
* **功能**：一键诊断 Windows 主机的开发环境健康状态。
* **参数**：无。
* **返回**：包含主机名、当前用户名、工作目录、Python 版本、Java 版本、Git 版本、Android SDK 是否就绪、AntGravity.exe 存在性等 JSON 格式字典。

### 18. `ag_file_list`
* **功能**：安全沙箱列出目录（支持 glob 通配符和递归）。
* **参数**：
  * `path` (str, 必填)：目标绝对路径（需在白名单内）。
  * `pattern` (str, 可选)：glob 过滤模式（默认 `*`）。
  * `recursive` (bool, 可选)：是否递归子目录。

### 19. `ag_file_read`
* **功能**：读取受控的文本文件（支持 UTF-8/GBK 自动适配，最大 512KB）。
* **参数**：
  * `path` (str, 必填)：绝对路径。
  * `encoding` (str, 可选)：默认 `utf-8`。

### 20. `ag_file_write`
* **功能**：安全写入文本内容，并自动补全缺失的父级目录。
* **参数**：
  * `path` (str, 必填)：绝对路径。
  * `content` (str, 必填)：写入内容。
  * `overwrite` (bool, 可选)：默认 True，覆盖同名文件。

### 21. `ag_file_exists`
* **功能**：快速探测路径是否存在，并告知其具体类型。
* **参数**：
  * `path` (str, 必填)。
* **返回**：`exists` (bool), `type` (`"file"`, `"dir"`, `"none"` 之一)。

### 22. `ag_powershell`
* **功能**：执行非管理员权限的任意多行命令，输出捕获最后 200 行。
* **参数**：
  * `command` (str, 必填)：PowerShell 指令。
  * `timeout` (int, 可选)：最大 600s。
  * `cwd` (str, 可选)：执行路径。
* **拦截逻辑**：拒绝 `rm -rf`、`Format-Volume`、`Stop-Computer` 等毁灭性操作。
* **支持工具链**：`python/pip`、`git`、`java/javac`、`gradlew`、`adb`、`docker`、`npm/npx`、`curl`。

---

## 📊 第五类：PowerPoint Office 办公自动化 (3 个)

基于 win32 COM 接口直接对 Windows 上处于活动状态的 PowerPoint 进行高级操作，规避了 OCR 容易定位错位的问题，精准率 100%。

### 23. `ag_pptx_read_slide`
* **功能**：抓取活动 PowerPoint 演示文稿中指定幻灯片的所有 Text Frame 文本和其各自的 Shape ID 列表。
* **参数**：
  * `slide_index` (int, 必填)：幻灯片索引（从 `1` 开始）。

### 24. `ag_pptx_fill_text`
* **功能**：根据指定的 Shape ID 完美填充或替换幻灯片中的占位文本，不破坏原有的精美排版和动画。
* **参数**：
  * `slide_index` (int, 必填)：幻灯片页码。
  * `shape_id` (int, 必填)：占位节点的 Shape ID。
  * `new_text` (str, 必填)：填充的文本内容。

### 25. `ag_pptx_create_slide`
* **功能**：在当前 PowerPoint 文档末尾新增一张幻灯片。
* **参数**：
  * `layout_index` (int, 可选)：幻灯片板式，默认 `12`（空白板式）。

---

## 🔒 全局安全约束

### 1. 文件系统白名单白名单目录
所有文件交互工具（无论是 `FileSystem` 还是以 `ag_file_*` 开头的专属工具）只能对以下根目录及其子目录进行操作：
- `D:\Obsidian\sync\task\` ── 各类任务库与 MCP 代码仓库
- `D:\dev\` ── 开发项目主目录
- `D:\AndroidProjects\` ── Android 项目主目录

### 2. 敏感环境目录拦截（黑名单）
以下目录已被安全切断，即便使用 `ag_powershell` 也会被底层监控拦截：
- `C:\Windows\`
- `C:\ProgramData\ssh\`
- `C:\Users\keche\.hermes\.env`

---

## 📡 远程 Hermes (192.168.0.126) 自动连接与测试步骤

已经在远程 Hermes 的 `~/.hermes/config.yaml` 中配置连接：
```yaml
mcpServers:
  antgravity-mcp:
    url: http://192.168.0.124:9000/mcp
    transport: streamable-http
```

### 让 Hermes 重新加载并开始测试
1. 在 Ubuntu 宿主机上重启 Hermes 容器：
   ```bash
   docker restart hermes
   ```
2. 重启后，由于 `AntGravityMCP` 系统服务正在后台坚固监听 `9000` 端口，Hermes 会**自动发起握手并建立两个长连接**。
3. 您可以向 Hermes 容器下达任意桌面或环境指令，例如：
   * *“帮我用 `ag_health_check` 看一下 Windows 上的 Python 版本”*
   * *“调用 `Screenshot` 帮我截一张图并分析”*
   * *“用 `ag_powershell` 检查一下 `adb devices` 识别情况”*
   * *“在 PowerPoint 中创建一张空白幻灯片并填入内容”*
