# GitHub Pages（github.io）发布报告历史

workflow: `.github/workflows/pages.yml`

- 每次 push main：
  - 运行 `factor-lab run ...`（可选）
  - 生成/更新 `runs/index.html`
  - 发布到 `gh-pages`

## Secrets（可选）
如果 Actions 里也要拉取行情：
- `BINANCE_API_KEY` / `BINANCE_API_SECRET`（可空）
- `HTTP_PROXY` / `HTTPS_PROXY`（如果需要）

## 建议
- 如果你不想每次 push 都跑回测：可以把 workflow 改成 `workflow_dispatch` + `schedule`。
