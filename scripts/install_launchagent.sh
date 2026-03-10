#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_PATH="$HOME/Library/LaunchAgents/ai.openclaw.factor-lab-pro.plist"
SCRIPT_PATH="$REPO_DIR/scripts/run_and_publish.sh"
LOG_DIR="$REPO_DIR/logs"
mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>ai.openclaw.factor-lab-pro</string>

    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>$SCRIPT_PATH</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$REPO_DIR</string>

    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
      <key>HOME</key>
      <string>$HOME</string>
      <key>DOCKER_HOST</key>
      <string>unix:///var/run/docker.sock</string>
      <key>FACTOR_LAB_RUN_MODE</key>
      <string>auto</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>StartCalendarInterval</key>
    <array>
      <dict><key>Minute</key><integer>0</integer></dict>
    </array>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/launchagent.out.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/launchagent.err.log</string>
  </dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/ai.openclaw.factor-lab-pro" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl enable "gui/$(id -u)/ai.openclaw.factor-lab-pro"
launchctl kickstart -k "gui/$(id -u)/ai.openclaw.factor-lab-pro"

echo "Installed: $PLIST_PATH"
launchctl print "gui/$(id -u)/ai.openclaw.factor-lab-pro" | sed -n '1,80p'
