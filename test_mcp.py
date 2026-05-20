"""MCP 端到端测试脚本 — 从本地验证所有 6 个工具"""
import requests
import json
import sys

BASE = "http://localhost:9000/mcp"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

def call(method, params=None, req_id=1):
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params:
        body["params"] = params
    r = requests.post(BASE, json=body, headers=HEADERS, timeout=30)
    # Parse SSE response
    session_id = r.headers.get("mcp-session-id")
    text = r.text
    for line in text.strip().split("\n"):
        if line.startswith("data: "):
            return json.loads(line[6:]), session_id, r.status_code
    return {"raw": text}, session_id, r.status_code

def call_with_session(method, params, session_id, req_id=1):
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params:
        body["params"] = params
    h = dict(HEADERS)
    if session_id:
        h["mcp-session-id"] = session_id
    r = requests.post(BASE, json=body, headers=h, timeout=30)
    text = r.text
    for line in text.strip().split("\n"):
        if line.startswith("data: "):
            return json.loads(line[6:]), r.status_code
    return {"raw": text}, r.status_code

print("=" * 60)
print("AntGravity MCP Server — 端到端测试")
print("=" * 60)

# Step 1: Initialize
print("\n[1/8] Initialize...")
resp, session_id, code = call("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"}
})
print(f"  Status: {code}")
print(f"  Session: {session_id}")
print(f"  Server: {resp.get('result', {}).get('serverInfo', {})}")
assert "result" in resp, f"Initialize failed: {resp}"

# Step 2: Send initialized notification
print("\n[2/8] Send initialized notification...")
body = {"jsonrpc": "2.0", "method": "notifications/initialized"}
h = dict(HEADERS)
if session_id:
    h["mcp-session-id"] = session_id
r = requests.post(BASE, json=body, headers=h, timeout=10)
print(f"  Status: {r.status_code}")

# Step 3: List tools
print("\n[3/8] List tools...")
resp, code = call_with_session("tools/list", {}, session_id, 2)
tools = resp.get("result", {}).get("tools", [])
print(f"  Status: {code}")
print(f"  Tools found: {len(tools)}")
for t in tools:
    print(f"    - {t['name']}: {t.get('description', '')[:60]}...")

# Step 4: ag_health_check
print("\n[4/8] ag_health_check...")
resp, code = call_with_session("tools/call", {
    "name": "ag_health_check",
    "arguments": {}
}, session_id, 3)
content = resp.get("result", {}).get("content", [])
if content:
    text = content[0].get("text", "")
    print(f"  Status: {code}")
    print(f"  Result (first 200 chars): {text[:200]}")
else:
    print(f"  Response: {json.dumps(resp, indent=2)[:300]}")

# Step 5: ag_file_list
print("\n[5/8] ag_file_list...")
resp, code = call_with_session("tools/call", {
    "name": "ag_file_list",
    "arguments": {"path": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server", "pattern": "*.py"}
}, session_id, 4)
content = resp.get("result", {}).get("content", [])
if content:
    text = content[0].get("text", "")
    print(f"  Status: {code}")
    print(f"  Result: {text[:300]}")
else:
    print(f"  Response: {json.dumps(resp, indent=2)[:300]}")

# Step 6: ag_file_read
print("\n[6/8] ag_file_read...")
resp, code = call_with_session("tools/call", {
    "name": "ag_file_read",
    "arguments": {"path": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server\\requirements.txt"}
}, session_id, 5)
content = resp.get("result", {}).get("content", [])
if content:
    text = content[0].get("text", "")
    print(f"  Status: {code}")
    print(f"  Result: {text[:200]}")
else:
    print(f"  Response: {json.dumps(resp, indent=2)[:300]}")

# Step 7: ag_file_exists
print("\n[7/8] ag_file_exists...")
resp, code = call_with_session("tools/call", {
    "name": "ag_file_exists",
    "arguments": {"path": "D:\\Obsidian\\sync\\task\\antgravity-mcp-server\\server.py"}
}, session_id, 6)
content = resp.get("result", {}).get("content", [])
if content:
    text = content[0].get("text", "")
    print(f"  Status: {code}")
    print(f"  Result: {text[:200]}")
else:
    print(f"  Response: {json.dumps(resp, indent=2)[:300]}")

# Step 8: ag_powershell
print("\n[8/8] ag_powershell...")
resp, code = call_with_session("tools/call", {
    "name": "ag_powershell",
    "arguments": {"command": "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"}
}, session_id, 7)
content = resp.get("result", {}).get("content", [])
if content:
    text = content[0].get("text", "")
    print(f"  Status: {code}")
    print(f"  Result: {text[:200]}")
else:
    print(f"  Response: {json.dumps(resp, indent=2)[:300]}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
