#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
RUN_DIR="$PROJECT_ROOT/.run"
QUIET="${1:-}"
STOPPED=0

kill_tree() {
  local parent="$1"
  if command -v pgrep >/dev/null 2>&1; then
    local children
    children="$(pgrep -P "$parent" 2>/dev/null || true)"
    for child in $children; do kill_tree "$child"; done
  fi
  kill "$parent" 2>/dev/null || true
}

for name in backend frontend; do
  PID_FILE="$RUN_DIR/$name.pid"
  [ -f "$PID_FILE" ] || continue
  PROCESS_ID="$(tr -cd '0-9' < "$PID_FILE")"
  if [ -n "$PROCESS_ID" ] && kill -0 "$PROCESS_ID" 2>/dev/null; then
    kill_tree "$PROCESS_ID"
    STOPPED=1
  fi
  rm -f "$PID_FILE"
done

if [ "$QUIET" != "--quiet" ]; then
  if [ "$STOPPED" -eq 1 ]; then echo "슬쩍 서버를 종료했습니다."
  else echo "실행 중인 슬쩍 서버를 찾지 못했습니다."
  fi
fi
