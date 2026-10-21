# BankViz — 在另一台电脑上部署

本指南用于把项目迁移到一台新机器（如演示用笔记本、导师机器、另一台宿舍电脑）。
全程本地运行，不需要任何云服务或账号。

## 0. 前置条件（需要先装好的软件）

| 软件 | 版本 | 用途 | 获取方式 |
|---|---|---|---|
| Python | 3.11+（推荐 3.12/3.13） | 后端运行 | https://www.python.org/downloads/ （安装时勾选 "Add Python to PATH"） |
| Node.js | 20+ | 前端构建/开发服务器 | https://nodejs.org （LTS 版即可） |
| Ollama | 最新版 | 本地运行 LLM | https://ollama.com/download （Windows 安装包） |

> 网络：只有**安装阶段**需要联网（下载依赖和模型）。**运行阶段完全离线**——
> 这正是项目的隐私卖点，演示前可以先拔网线/关 Wi-Fi 证明给导师看。

## 1. 拿到代码

任选其一：

```bash
# 方式 A：从 GitLab 克隆（推送到远程仓库之后）
git clone https://stgit.dcs.gla.ac.uk/msc-project-for-information-technology/2025/it-project-<GUID>/<GUID>-development-project.git
cd <GUID>-development-project

# 方式 B：直接拷贝整个 E:\bank-viz-tool 文件夹到 U 盘/网盘
# （拷贝时可排除 backend\.venv 和 frontend\node_modules —— 都会重新生成）
```

## 2. 一键安装（Windows）

```bat
:: 在项目根目录，双击或命令行运行：
setup_local.bat
```

它会自动完成：创建 Python 虚拟环境 → 安装后端依赖 → 安装前端依赖 → 检查 Ollama 和模型。

**手动安装**（Mac/Linux 或想分步执行时）：

```bash
# 后端
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

## 3. 安装 LLM（可选但推荐）

```bash
# 安装 Ollama 后，拉取模型（约 1.9 GB，只需一次）
ollama pull qwen2.5:3b

# 启动 Ollama 服务（Windows 开始菜单打开 Ollama 即可，或命令行）
ollama serve
```

- 有 GPU 的机器可以拉 `qwen2.5:7b` 并设置环境变量 `OLLAMA_MODEL=qwen2.5:7b`（效果更好）
- **不装 Ollama 也能运行**：系统自动进入统计兜底模式（降级），图表照常生成，
  只有"LLM 生成计划"这一环节换成本地统计规则推荐器

## 4. 启动

```bat
:: Windows 一键启动（根目录）：
run_local.bat
```

它会开两个窗口（后端 :8000、前端 :5173）并自动打开浏览器 `http://localhost:5173`。

**手动启动**（两个终端）：

```bash
# 终端 1：后端
cd backend
.venv\Scripts\python -m uvicorn app.main:app --port 8000

# 终端 2：前端
cd frontend
npm run dev
```

打开 http://localhost:5173 → 上传 `data/sample_bank_customers.csv`（或任意 CSV/Excel）→ 使用。

## 5. 可配置环境变量（一般不用动）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:3b` | LLM 模型名（有 GPU 可换 7b） |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama 地址（**只允许 localhost**，非本地端点会拒绝启动） |
| `OLLAMA_TIMEOUT` | `300` | LLM 单次请求超时（秒） |

Windows 设置方法（启动后端前）：`set OLLAMA_MODEL=qwen2.5:7b`

## 6. 演示前检查清单（26 日会议用）

- [ ] `setup_local.bat` 已跑过，`run_local.bat` 能正常拉起两个窗口
- [ ] Ollama 正在运行（后台托盘有羊驼图标，或 `curl http://127.0.0.1:11434/api/version` 有响应）
- [ ] **预热 LLM**：上传数据后先点一次 "Auto-generate"，首次调用含模型加载约 1–2 分钟，之后每次约 30 秒
- [ ] 备一个不依赖 LLM 的演示路径：前端三个页面 + 手动图表模式（零 LLM 依赖，秒出图），万一 LLM 环节出问题不至于冷场
- [ ] 可以当着导师面断网演示隐私特性（运行期无任何外部请求）

## 7. 常见问题

| 现象 | 原因与解决 |
|---|---|
| 后端报 "Local LLM detected" 前有 WARN / degraded_mode: true | Ollama 没启动，或没拉模型。启动 Ollama / `ollama pull qwen2.5:3b` |
| Ollama 起了但 `ollama list` 为空 | 模型目录不在默认位置。设置环境变量 `OLLAMA_MODELS=<模型目录>` 再启动（本机原路径 `D:\Ollama\models` 只在装了 Ollama 的那台机器有效，新机器默认路径即可） |
| 端口 8000/5173 被占用 | 关掉占用进程，或换端口：后端 `--port 8001`，前端 `vite.config.js` 里改 `server.port`（注意同步代理目标端口） |
| 自动生成的图表很少/报 "degraded" | 大概率 LLM 超时。查看后端窗口日志；机器太慢就保持 3b 模型，别换 7b |
| npm install 很慢 | 国内网络可用 `npm config set registry https://registry.npmmirror.com` 后重试 |
| 公司/校园代理环境 | 后端已内置 `trust_env=False` 绕过代理访问 localhost，一般无需处理；若 curl 测试不通，加 `--noproxy '*'` |

## 8. 运行测试（可选，证明代码质量）

```bash
cd backend
.venv\Scripts\python -m pytest tests/ -q
# 预期输出：40 passed
```
