# Hermes 审批协议

## AntGravity → Hermes API 调用

| 项目 | 值 |
|------|-----|
| API 地址 | `http://192.168.0.124:8642/v1/chat/completions` |
| Token | （需配置，见下方） |
| 触发标记 | 消息中包含 `[需要审批]` |

## 调用示例

```python
import requests

url = "http://192.168.0.124:8642/v1/chat/completions"
headers = {
    "Authorization": "Bearer <你的Token>",
    "Content-Type": "application/json"
}
payload = {
    "model": "any",
    "messages": [
        {"role": "user", "content": "执行 git push [需要审批]"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

## Token 配置

在 AntGravity 端配置环境变量或直接填入请求头：

```
Authorization: Bearer <Hermes_API_Token>
```

Token 值在 Hermes 容器的 `/opt/data/.env` 文件里，变量名可能是 `HERMES_API_KEY` 或类似名称。

## 审批流程

1. AntGravity 发送消息带 `[需要审批]` 标记
2. Hermes 收到后，同时推送审批请求到：
   - 钉钉（Interactive Card）
   - 飞书（Interactive Card）
3. 用户点击「同意」或「拒绝」
4. Hermes 返回结果给 AntGravity

## 按钮交互

审批卡片带两个按钮：
- 「同意」→ 执行操作
- 「拒绝」→ 取消操作

用户点击后，Hermes 会把结果发回给 AntGravity。