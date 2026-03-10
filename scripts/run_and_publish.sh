#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNS_DIR="$REPO_DIR/runs"
LOG_DIR="$REPO_DIR/logs"
VENV_DIR="$REPO_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
RUN_LOG="$LOG_DIR/local-run-$(date +%Y%m%d-%H%M%S).log"
CONFIG_PATH="${FACTOR_LAB_CONFIG:-$REPO_DIR/configs/demo.yaml}"
PUBLISH_BRANCH="${FACTOR_LAB_PUBLISH_BRANCH:-gh-pages}"
PUBLISH_REMOTE="${FACTOR_LAB_PUBLISH_REMOTE:-origin}"
PUBLISH_TMP_ROOT="${TMPDIR:-/tmp}"
RUN_MODE="${FACTOR_LAB_RUN_MODE:-auto}"

mkdir -p "$RUNS_DIR" "$LOG_DIR"
exec > >(tee -a "$RUN_LOG") 2>&1

echo "[$(date '+%F %T')] repo=$REPO_DIR"
echo "[$(date '+%F %T')] config=$CONFIG_PATH"

cd "$REPO_DIR"

analyze_previous_run() {
  echo "[$(date '+%F %T')] analyzing previous run for optimization hints"
  python3 - <<'PY'
import json
from pathlib import Path
from datetime import datetime

runs_dir = Path("runs")
out = Path("logs/pre_run_analysis.md")
out.parent.mkdir(parents=True, exist_ok=True)

run_dirs = [p for p in runs_dir.iterdir() if p.is_dir() and p.name not in {"cache", "latest"}]
run_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)

lines = [f"# Pre-run analysis ({datetime.now().isoformat(timespec='seconds')})", ""]

if not run_dirs:
    lines.append("No previous run found. Start with default config and collect baseline.")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out.as_posix())
    raise SystemExit(0)

last = run_dirs[0]
ledger = last / "ledger.jsonl"
lines.append(f"Last run: `{last.name}`")

if not ledger.exists():
    lines.append("No ledger.jsonl found. Keep current config and verify run integrity first.")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out.as_posix())
    raise SystemExit(0)

rows = []
with ledger.open("r", encoding="utf-8") as f:
    for line in f:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass

if not rows:
    lines.append("Ledger is empty/invalid. Keep config, fix data pipeline stability first.")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out.as_posix())
    raise SystemExit(0)

# core stats
ok = [r for r in rows if r.get("status") == "ok"]
hold = [r for r in rows if r.get("status") == "hold"]
rets = [float(r.get("ret", 0.0)) for r in ok if isinstance(r.get("ret", 0), (int, float))]
equities = [float(r.get("equity", 1.0)) for r in rows if isinstance(r.get("equity", 1), (int, float))]

final_eq = equities[-1] if equities else 1.0
total_ret = final_eq - 1.0
peak = 1.0
max_dd = 0.0
for e in equities:
    peak = max(peak, e)
    dd = e / peak - 1.0
    max_dd = min(max_dd, dd)

win_rate = (sum(1 for x in rets if x > 0) / len(rets)) if rets else 0.0

lines += [
    "",
    "## Snapshot",
    f"- final equity: **{final_eq:.4f}**",
    f"- total return: **{total_ret*100:.2f}%**",
    f"- max drawdown: **{max_dd*100:.2f}%**",
    f"- win rate (ok steps): **{win_rate*100:.1f}%**",
    f"- ok steps: **{len(ok)}** / all steps: **{len(rows)}**",
    f"- hold ratio: **{(len(hold)/len(rows)*100 if rows else 0):.1f}%**",
]

lines += ["", "## Optimization hints for next run"]

if total_ret <= 0:
    lines.append("- Return <= 0: lower turnover pressure first (e.g., reduce rebalance frequency or raise lam_tc).")
if max_dd < -0.25:
    lines.append("- Drawdown too deep: reduce concentration/risk (e.g., lower w_max or increase lam_risk).")
if rets and win_rate < 0.45:
    lines.append("- Low win rate: check if strategy relies on rare outliers; tighten factor quality filter (ic_min_abs/icir_min_abs).")
if rows and len(hold)/len(rows) > 0.9:
    lines.append("- Hold ratio very high: refresh signal cadence may be too slow; evaluate rebalance_period/fwd_period trade-off.")
if len(ok) < 30:
    lines.append("- Too few effective trading steps: extend sample window (more days) before drawing conclusions.")

if lines[-1] == "## Optimization hints for next run":
    lines.append("- No obvious red flags. Keep current config and continue collecting more out-of-sample runs.")

out.write_text("\n".join(lines), encoding="utf-8")
print(out.as_posix())
PY
}

analyze_previous_run

run_local_python() {
  if [ ! -x "$PYTHON_BIN" ]; then
    echo "[$(date '+%F %T')] creating virtualenv"
    if command -v python3.11 >/dev/null 2>&1; then
      python3.11 -m venv "$VENV_DIR"
    else
      python3 -m venv "$VENV_DIR"
    fi
  fi

  if ! "$PYTHON_BIN" -c 'import sys; assert (3,10) <= sys.version_info[:2] < (3,13)' >/dev/null 2>&1; then
    rm -rf "$VENV_DIR"
    if command -v python3.11 >/dev/null 2>&1; then
      echo "[$(date '+%F %T')] recreating virtualenv with python3.11"
      python3.11 -m venv "$VENV_DIR"
    else
      return 1
    fi
  fi

  if ! "$PYTHON_BIN" -c 'import sys; assert (3,10) <= sys.version_info[:2] < (3,13)' >/dev/null 2>&1; then
    return 1
  fi

  if ! "$PYTHON_BIN" -c 'import numpy, pandas, factor_lab.cli' >/dev/null 2>&1; then
    echo "[$(date '+%F %T')] installing/updating dependencies"
    "$PIP_BIN" install --upgrade pip
    "$PIP_BIN" install .
  fi

  echo "[$(date '+%F %T')] running factor_lab via local python"
  "$PYTHON_BIN" -m factor_lab run -c "$CONFIG_PATH"
}

run_docker() {
  echo "[$(date '+%F %T')] running factor_lab via docker compose"
  docker compose build factor-lab-pro
  docker compose run --rm factor-lab-pro
}

case "$RUN_MODE" in
  auto)
    if ! run_local_python; then
      echo "[$(date '+%F %T')] local python unavailable/incompatible; falling back to docker"
      run_docker
    fi
    ;;
  local)
    run_local_python
    ;;
  docker)
    run_docker
    ;;
  *)
    echo "Unknown FACTOR_LAB_RUN_MODE: $RUN_MODE" >&2
    exit 2
    ;;
esac

if [ ! -f "$RUNS_DIR/index.html" ]; then
  echo "runs/index.html was not generated" >&2
  exit 1
fi

echo "[$(date '+%F %T')] preparing gh-pages publish"
PUBLISH_DIR="$(mktemp -d "$PUBLISH_TMP_ROOT/factor-lab-pages.XXXXXX")"
trap 'rm -rf "$PUBLISH_DIR"' EXIT

if git ls-remote --exit-code --heads "$PUBLISH_REMOTE" "$PUBLISH_BRANCH" >/dev/null 2>&1; then
  git clone --depth 1 --branch "$PUBLISH_BRANCH" "$(git remote get-url "$PUBLISH_REMOTE")" "$PUBLISH_DIR"
else
  git clone --depth 1 "$(git remote get-url "$PUBLISH_REMOTE")" "$PUBLISH_DIR"
  cd "$PUBLISH_DIR"
  git checkout --orphan "$PUBLISH_BRANCH"
  git rm -rf . >/dev/null 2>&1 || true
  cd "$REPO_DIR"
fi

find "$PUBLISH_DIR" -mindepth 1 -maxdepth 1 \
  ! -name .git \
  ! -name .github \
  -exec rm -rf {} +
cp -R "$RUNS_DIR"/. "$PUBLISH_DIR"/
touch "$PUBLISH_DIR/.nojekyll"

echo "[$(date '+%F %T')] committing gh-pages content"
cd "$PUBLISH_DIR"
git checkout "$PUBLISH_BRANCH" >/dev/null 2>&1 || true
git add -A
if git diff --cached --quiet; then
  echo "[$(date '+%F %T')] no changes to publish"
  exit 0
fi

git config user.name "factor-lab-bot"
git config user.email "factor-lab-bot@users.noreply.github.com"
git commit -m "publish: $(date '+%F %T')"
git push "$PUBLISH_REMOTE" "$PUBLISH_BRANCH"

echo "[$(date '+%F %T')] publish complete"
