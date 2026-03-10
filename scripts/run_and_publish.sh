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

run_local_python() {
  if [ ! -x "$PYTHON_BIN" ]; then
    echo "[$(date '+%F %T')] creating virtualenv"
    python3 -m venv "$VENV_DIR"
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

rm -rf "$PUBLISH_DIR"/* "$PUBLISH_DIR"/.[!.]* "$PUBLISH_DIR"/..?* 2>/dev/null || true
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
