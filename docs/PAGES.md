# GitHub Pages（github.io）发布报告历史

主发布方式：**本机定时运行 + 推送 `gh-pages`**

相关脚本：
- `scripts/run_and_publish.sh`：本机执行回测并发布 Pages
- `scripts/install_launchagent.sh`：安装 macOS `launchd` 定时任务（默认每天 00:17 / 06:17 / 12:17 / 18:17）

GitHub Actions 中的 `.github/workflows/pages.yml` 仅保留 `workflow_dispatch`，作为手动诊断/补跑入口，不再依赖 GitHub runner 抓 Binance 数据。

## Pages 设置
在仓库 Settings -> Pages：
- Source 选择 **Deploy from a branch**
- Branch 选择 **gh-pages** / root

## 本机部署
```bash
bash scripts/install_launchagent.sh
```

## 手动跑并发布
```bash
bash scripts/run_and_publish.sh
```

## Secrets（可选）
如果 Actions 里也要拉取行情：
- `BINANCE_API_KEY` / `BINANCE_API_SECRET`（可空）
- `HTTP_PROXY` / `HTTPS_PROXY`（如果需要）

## 自检
另有 `.github/workflows/smoke.yml`：
- 先跑 `python -m factor_lab doctor`
- 再用 `configs/smoke.yaml` 做快速样本回测
- 用来尽早发现主流程退化
