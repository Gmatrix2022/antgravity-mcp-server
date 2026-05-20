# Hermes ↔ AntGravity 集成说明

## 1. GitHub 自动上架流程

### Token 配置
把 GitHub Personal Access Token 填入 `.env`：
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

**Token 申请地址**：https://github.com/settings/tokens

**需要的权限**：
- `repo`（全部）
- `workflow`（如果触发 GitHub Actions）

### 自动上架步骤
```powershell
cd D:\Obsidian\sync\task\<项目目录>

# 初始化 git（如果还没有）
git init
git add .
git commit -m "initial commit"

# 设置远程仓库（替换 <token> 和 <owner/repo>）
git remote set-url origin https://<token>@github.com/<owner>/<repo>.git

# 推送
git push -u origin HEAD
```

### 关键文件位置
- GitHub Token 存档：`D:\Obsidian\sync\task\antgravity-mcp-server\docs\TOKEN.md`
- Hermes GitHub Skills：`D:\Obsidian\sync\task\antgravity-mcp-server\docs\GITHUB_SKILLS.md`

---

## 2. Hermes Skills 存放位置

### Skills 主目录
```
D:\Obsidian\sync\task\antgravity-mcp-server\docs\SKILLS_INDEX.md
```

### 常用 Skills
| 路径 | 说明 |
|------|------|
| `D:\Obsidian\sync\task\hermes-agent\` | Hermes Agent 配置 |
| `D:\Obsidian\sync\task\hermes-agent\docs\` | Skills 列表 |

### 记忆系统
| 路径 | 说明 |
|------|------|
| `D:\Obsidian\sync\task\hermes-memory\` | 用户偏好、历史交互 |

---

## 3. 通过 MCP 协作流程

Hermes 可以通过 MCP 工具操作 AntGravity：
- `ag_powershell` - 执行 PowerShell 命令
- `ag_file_read/write` - 读写文件
- `ag_health_check` - 健康检查

如果 Hermes 需要在 Windows 上执行 Git 操作，调用 `ag_powershell` 即可。