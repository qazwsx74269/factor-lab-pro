# Factor Lab Pro — 自动挖掘因子 / 回测 / 汇报 / GitHub Pages（工程版）

你选择了 **B（工程版）**：这份仓库从“研究脚本”升级为 **可长期迭代的小型量化平台骨架**：
- ✅ 数据：Binance 公共 K 线（Spot 示例） + 本地缓存（parquet）
- ✅ 因子：多时间框架因子注册表 + 自动挖掘（IC/ICIR）
- ✅ 研究：去极值/标准化/去共线（正交） + 稳健 IC
- ✅ 组合：因子权重 **凸优化（CVXPy）**（稀疏/风险/换手惩罚）
- ✅ 策略：**3–10 策略池**（健康评分、淘汰替换、分配器）
- ✅ 回测：截面 Top/Bottom 多空 + 成本拆分（fee/slip/impact）
- ✅ 汇报：生成 HTML（含图表） + 自动归档每次运行 + `runs/index.html`
- ✅ github.io：GitHub Actions 自动发布 **每次汇报历史索引页**

> 我无法直接替你“创建/推送 GitHub 仓库”（当前 GitHub 连接器只读），但我已生成完整工程仓库 zip。
> 你解压后按 `Quick Start` 推送到 GitHub 即可。
>
> 你的 GitHub 用户名（来自已连接信息）：`qazwsx74269`

---

## Quick Start

### 1) 安装（Poetry）
```bash
cd factor-lab-pro
poetry install
cp .env.example .env
poetry run factor-lab run -c configs/demo.yaml
```

输出：
- `runs/<timestamp>/report.html`
- `runs/latest/report.html`
- `runs/index.html`（历史索引）

### 2) 一键启动（Docker）
```bash
cp .env.example .env
docker compose up --build
```

---

## Binance API / 代理配置

### 只拉行情（默认）
使用 spot 公共接口 `/api/v3/klines`，不需要 key。

### 代理
三选一：
1) 环境变量：
```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
```

2) `.env`：
```
HTTPS_PROXY=http://127.0.0.1:7890
HTTP_PROXY=http://127.0.0.1:7890
```

3) `configs/*.yaml`：`data.binance.proxy`

---

## GitHub Pages（github.io）发布每次汇报

仓库带 `.github/workflows/pages.yml`：
- push `main` 后：会运行回测（可选），生成 `runs/index.html` 并发布到 `gh-pages`

开启 Pages：
1) Settings -> Pages
2) Build and deployment -> Source：选择 **Deploy from a branch**
3) Branch：选择 **gh-pages / root**
4) 访问：`https://<you>.github.io/<repo>/`

默认自动化：
- **本机 launchd**：每 6 小时自动跑一次并发布到 `gh-pages`
- GitHub Actions `workflow_dispatch`：保留为手动诊断/补跑入口
- `Smoke Test` workflow：先做运行环境自检；如果配置了代理 secrets，再跑 `configs/smoke.yaml` 小样本回测

本机无人值守发布：
```bash
bash scripts/install_launchagent.sh
```

手动立即跑一次：
```bash
bash scripts/run_and_publish.sh
```

---

## 目录结构（工程版）

```
factor-lab-pro/
  factor_lab/                 # 主包
    cli.py                    # CLI：run/search/doctor
    config/                   # pydantic 配置模型 + 校验
    data/                     # Binance + 缓存 + panel builder
    factors/                  # 因子注册表 + 自动挖掘
    research/                 # IC/ICIR + 正交 + winsorize
    optimizer/                # 凸优化权重（cvxpy）
    strategy/                 # 3-10 策略池（健康/替换/分配）
    backtest/                 # 回测引擎 + 成本拆分
    report/                   # HTML 报告 + runs index
    utils/                    # 日志、时间、指标等
  configs/
  docs/
  scripts/
  runs/                       # 输出目录（默认）
  .github/workflows/
```

---

## 免责声明
本仓库仅供研究与教育用途，不构成投资建议；请自行评估风险。
