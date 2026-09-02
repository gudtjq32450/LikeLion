#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
RUN_DIR="$PROJECT_ROOT/.run"
PYTHON="$BACKEND_DIR/.venv/bin/python"

echo "슬쩍 서버를 준비합니다..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3가 필요합니다: https://python.org"
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "Node.js와 npm이 필요합니다: https://nodejs.org"
  exit 1
fi

if [ ! -x "$PYTHON" ]; then
  echo "[1/4] Python 가상환경을 만듭니다."
  python3 -m venv "$BACKEND_DIR/.venv"
fi

if ! "$PYTHON" -c 'import fastapi, uvicorn' >/dev/null 2>&1; then
  echo "[2/4] 백엔드 패키지를 설치합니다."
  "$PYTHON" -m pip install -r "$BACKEND_DIR/requirements.txt"
else
  echo "[2/4] 백엔드 패키지가 준비되어 있습니다."
fi

if [ ! -x "$FRONTEND_DIR/node_modules/.bin/vite" ]; then
  echo "[3/4] 프런트엔드 패키지를 설치합니다."
  (cd "$FRONTEND_DIR" && npm install --no-audit --no-fund)
else
  echo "[3/4] 프런트엔드 패키지가 준비되어 있습니다."
fi

mkdir -p "$RUN_DIR"

if command -v lsof >/dev/null 2>&1; then
  for port in 8000 5173; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "포트 $port 가 이미 사용 중입니다. stop-macos.command를 실행하거나 기존 서버를 종료하세요."
      exit 1
    fi
  done
fi

echo "[4/4] 백엔드와 프런트엔드를 시작합니다."
(cd "$BACKEND_DIR" && nohup "$PYTHON" -m uvicorn main:app --host 127.0.0.1 --port 8000 > "$RUN_DIR/backend.log" 2>&1 & echo $! > "$RUN_DIR/backend.pid")
(cd "$FRONTEND_DIR" && nohup npm run dev -- --host 127.0.0.1 > "$RUN_DIR/frontend.log" 2>&1 & echo $! > "$RUN_DIR/frontend.pid")

READY=0
for _ in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 0.5
done

if [ "$READY" -ne 1 ]; then
  bash "$PROJECT_ROOT/stop-macos.command" --quiet || true
  echo "백엔드가 제한 시간 안에 시작되지 않았습니다. $RUN_DIR/backend.log를 확인하세요."
  exit 1
fi

sleep 1
open http://localhost:5173
echo
echo "슬쩍이 실행되었습니다: http://localhost:5173"
echo "종료하려면 stop-macos.command를 실행하세요."
echo "이 창은 닫아도 서버가 유지됩니다."
