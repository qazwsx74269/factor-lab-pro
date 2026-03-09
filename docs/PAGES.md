# GitHub Pages（github.io）发布报告历史

主 workflow: `.github/workflows/pages.yml`

触发方式：
- push `main`
- `schedule`（默认每 6 小时一次）
- `workflow_dispatch`

流程：
1. 安装项目依赖
2. 运行 `python -m factor_lab run -c configs/demo.yaml`
3. 若成功，发布 `runs/` 到 GitHub Pages
4. 若失败，仍然发布一个诊断页，并把 `runs/action-run.log` 暴露出来，避免页面直接空白

## Pages 设置
在仓库 Settings -> Pages：
- Source 选择 **GitHub Actions**

## Secrets（可选）
如果 Actions 里也要拉取行情：
- `BINANCE_API_KEY` / `BINANCE_API_SECRET`（可空）
- `HTTP_PROXY` / `HTTPS_PROXY`（如果需要）

## 自检
另有 `.github/workflows/smoke.yml`：
- 先跑 `python -m factor_lab doctor`
- 再用 `configs/smoke.yaml` 做快速样本回测
- 用来尽早发现主流程退化
