# Like Lion Hackathon

가족을 주제로 진행하는 Like Lion Hackathon 프로젝트입니다.

## 🛠 Tech Stack

## 서버실행

### 원클릭 실행

Windows에서는 프로젝트 루트의 `start-windows.bat`을 더블클릭합니다.
종료할 때는 `stop-windows.bat`을 실행합니다.

macOS에서는 최초 한 번 실행 권한을 부여한 뒤 `start-macos.command`를 더블클릭합니다.

```bash
chmod +x start-macos.command stop-macos.command
```

종료할 때는 `stop-macos.command`를 실행합니다.

실행 파일은 최초 실행 시 Python 가상환경과 npm 패키지를 자동으로 준비하고,
백엔드와 프런트엔드를 함께 시작한 뒤 `http://localhost:5173`을 엽니다.

### 직접 실행

backend 터미널: `uvicorn main:app --reload`

frontend 터미널: `npm run dev`

### Frontend

- React
- Vite
- JavaScript
- Oxlint
- Node.js 24.x
- npm 11.x

### Backend

- Python 3.11.x
- FastAPI
- Uvicorn

---

## 📁 Project Structure

```text
like_lion/
├── backend/
│   ├── .venv/
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

> `.venv`, `node_modules`, `.env` 등의 파일은 Git에 포함하지 않습니다.

---

# 🚀 Getting Started

## 1. Repository Clone

```bash
git clone <repository-url>
cd like_lion
```

---

## 2. Backend Setup

### Requirements

Python `3.11.x` 사용을 권장합니다.

버전 확인:

```bash
python3 --version
```

또는:

```bash
python --version
```

### 가상환경 생성

macOS / Linux:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
```

가상환경이 활성화되면 터미널에 다음과 같이 표시됩니다.

```text
(.venv)
```

### Python 패키지 설치

```bash
pip install -r requirements.txt
```

### FastAPI 실행

```bash
uvicorn main:app --reload
```

서버:

```text
http://127.0.0.1:8000
```

API 문서:

```text
http://127.0.0.1:8000/docs
```

---

## 3. Frontend Setup

새 터미널을 열고 프로젝트의 `frontend` 디렉토리로 이동합니다.

```bash
cd frontend
```

패키지 설치:

```bash
npm install
```

개발 서버 실행:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔗 Local Development

개발 시 Backend와 Frontend 서버를 각각 실행해야 합니다.

### Terminal 1 — Backend

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

Windows:

```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload
```

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

실행 구조:

```text
Browser
   │
   ▼
React + Vite
localhost:5173
   │
   │ HTTP Request
   ▼
FastAPI
127.0.0.1:8000
```

---

# 🌿 Git Convention

## Branch

```text
main
develop
feature/*
fix/*
```

예시:

```text
feature/login
feature/family
feature/memory
fix/login-error
```

기능 개발은 별도의 브랜치에서 진행하고 완료 후 `develop` 브랜치에 병합합니다.

---

## Commit Convention

| Type       | Description           |
| ---------- | --------------------- |
| `feat`     | 새로운 기능           |
| `fix`      | 버그 수정             |
| `design`   | UI/CSS 수정           |
| `refactor` | 코드 리팩토링         |
| `docs`     | 문서 수정             |
| `test`     | 테스트 코드           |
| `chore`    | 환경설정 및 기타 작업 |

예시:

```bash
git commit -m "feat: 가족 생성 API 구현"
git commit -m "design: 메인 페이지 UI 구현"
git commit -m "fix: 로그인 요청 오류 수정"
git commit -m "docs: README 개발환경 추가"
```

---

# 🔐 Environment Variables

API Key, Secret Key 등의 민감한 정보는 GitHub에 업로드하지 않습니다.

각자 로컬에서 `.env` 파일을 생성하여 사용합니다.

```text
.env
```

공유가 필요한 환경변수 이름은 `.env.example`을 통해 관리합니다.

예시:

```env
API_KEY=
DATABASE_URL=
```

실제 Key 값은 절대 Git에 Commit하지 않습니다.

---

# ⚠️ Before Commit

커밋하기 전에 반드시 확인합니다.

```bash
git status
```

다음 파일 및 디렉토리가 포함되지 않았는지 확인합니다.

```text
.venv/
node_modules/
.env
.DS_Store
Thumbs.db
Desktop.ini
```

---

# 👥 Collaboration

작업 시작 전:

```bash
git pull
```

새로운 기능 개발:

```bash
git checkout -b feature/기능명
```

작업 완료:

```bash
git add .
git commit -m "feat: 기능 설명"
git push origin feature/기능명
```

이후 Pull Request를 생성하여 코드를 병합합니다.
