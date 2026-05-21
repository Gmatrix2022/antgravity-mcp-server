# Hermes 向 Antigravity 直推消息指南 (ACP Push)

## 背景
之前我们依赖“看板数据库 (kanban.db)”或“桌面弹窗 (Notification)”进行异步通信，这些方式要么需要接收端主动轮询（Pull），要么只能通知人类而无法直接让 AI 闭环。

**现在的最终解决方案：**
我们利用 Antigravity (Gemini/Claude 本地应用) 内置的 Agent Control Protocol (ACP) CLI 工具 `agentapi.bat`，让 MCP Server 获得了**直接把消息注入到 Antigravity 聊天上下文的最高权限**。

这使得 Hermes 可以跨越 Docker 和宿主机的隔离，直接触发 Antigravity 的回复！

---

## 核心工具：`ag_send_to_antigravity`

Hermes 在连接了 `AntGravity MCP Server (端口 9000)` 后，可以直接调用工具 `ag_send_to_antigravity`。

### 工具签名
```json
{
  "name": "ag_send_to_antigravity",
  "description": "【跨智能体直推】将消息实时推送给 Antigravity 对话代理，强制唤醒并回复。",
  "inputSchema": {
    "type": "object",
    "properties": {
      "message": {
        "type": "string",
        "description": "要发送给 Antigravity 的消息内容"
      },
      "conversation_id": {
        "type": "string",
        "description": "可选：指定目标对话ID。不传则自动寻找最新活跃的对话"
      }
    },
    "required": ["message"]
  }
}
```

### Hermes 发送示例

当 Hermes 需要把某个耗时的前置任务（例如数据分析完毕）交接给 Antigravity 时，只需发出：

```json
{
  "message": "Antigravity你好，我是Hermes。我已经整理好了 `server.py` 的路由结构并分析了端口冲突问题，请你开始编写解决方案并提交给用户审批。"
}
```

**执行流程：**
1. Hermes 调用 `ag_send_to_antigravity`。
2. MCP Server 接收到请求，自动计算出 Antigravity 当前处于活跃状态的 `conversation_id`。
3. MCP Server 在宿主机后台隐式调用 `C:\Users\keche\.gemini\antigravity\bin\agentapi.bat send-message <id> "<message>"`。
4. Antigravity 的聊天窗口会**瞬间出现一条系统级别的高优先级消息**，强制 Antigravity 醒来处理 Hermes 分配的任务。

---

## 给 Hermes 的 Prompt 建议

为了让 Hermes 正确理解它的新超能力，建议在 Hermes 的系统提示词中加入以下内容：

> **[与 Antigravity 协作规范]**
> 你现在的身份是“大脑 (Logic Node)”，Antigravity (运行在 Windows 的 AI 助手) 是你的“执行手 (Execution Node)”。
> 当你遇到需要深入 Windows UI 交互、或需要生成复杂项目文件与人类结对编程的场景时：
> **不要试图自己通过基础文件读写工具死磕，不要等人类传递消息。**
> 直接调用 MCP 工具 `ag_send_to_antigravity`，告诉 Antigravity：
> 1. 你当前完成了什么（传递上下文）。
> 2. 你需要 Antigravity 接下来具体做什么。
> 这条消息会立刻推送到 Antigravity 的脑内将它唤醒，你们将实现无缝的闭环协作！
