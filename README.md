# 슬쩍

> 말하기 어려운 자녀의 고민을 자연스러운 질문으로 바꾸고, 부모의 경험이 담긴 답변을 가족에게 전하기 좋은 문장으로 다듬는 가족 대화 프로토타입

슬쩍은 자녀가 입력한 고민의 핵심 의도를 익명화한 뒤 네 개의 일상 질문 사이에 섞어 보여줍니다. 부모는 질문 하나를 골라 자신의 경험을 답하고, 답변을 부드럽게 다듬어 지혜 서재에 보관할 수 있습니다.

## 주요 기능

- 자녀의 감정과 고민 입력
- `슬쩍 모드`와 `살짝 모드` 선택
- 자녀의 고민을 부모의 과거 경험을 묻는 질문으로 변환
- 변환된 질문 한 개를 네 개의 일상 질문과 섞어서 제공
- 질문 내용에 맞는 답변 시작 문구 제공
- 부모 답변을 질문 의도에 맞게 다듬기
- 감정, 날짜, 질문, 원문, 다듬은 답변을 지혜 서재에 표시
- OpenAI API를 사용할 수 없을 때 로컬 질문·답변 규칙으로 대체

## 현재 구현 범위

현재 버전은 한 브라우저에서 자녀 화면과 부모 화면을 전환하는 시연용 프로토타입입니다.

- 지혜 서재 데이터는 브라우저 `localStorage`에 저장됩니다.
- 질문 변환 결과는 React 상태에만 저장되므로 새로고침하면 사라질 수 있습니다.
- 음성 녹음 버튼은 실제 음성 인식이 아니라 예시 답변을 입력하는 데모 동작입니다.
- 로그인, 사용자 인증, 부모·자녀 계정 구분은 아직 없습니다.
- 가족 생성, 초대 코드, 가족 구성원 관리는 아직 없습니다.
- 데이터베이스와 다른 PC·휴대폰 사이의 질문 전달·동기화는 아직 없습니다.
- 질문의 대기·열람·답변 완료 상태도 서버에서 관리하지 않습니다.

실제 가족 간 서비스로 확장하려면 인증, 가족 멤버십, 질문 전달 상태, 답변 저장을 담당하는 데이터베이스가 필요합니다.

## 기술 구성

| 영역 | 기술 |
| --- | --- |
| Frontend | React 19, Vite 8, JavaScript, CSS |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| AI | OpenAI Responses API, JSON Schema 구조화 출력 |
| Local fallback | Python 질문 은행과 답변 다듬기 규칙 |
| 현재 저장소 | 브라우저 `localStorage` |

## 실행 요구사항

- Python 3.10 이상
- Node.js `^20.19.0` 또는 `>=22.12.0`
- npm
- 최초 패키지 설치를 위한 인터넷 연결
- AI 기능 사용 시 OpenAI API 키

## 빠른 실행

### Windows

현재 Windows 실행 파일은 백엔드와 프런트엔드가 분리되어 있습니다.

1. 프로젝트 루트의 `START.bat`을 실행해 백엔드를 켭니다.
2. 첫 번째 창을 닫지 않은 상태에서 `START2.bat`을 실행해 프런트엔드를 켭니다.
3. 브라우저에서 `http://localhost:5173`을 엽니다.

각 실행 파일은 처음 실행할 때 필요한 가상환경 또는 npm 패키지를 준비합니다.

### macOS / Linux

터미널 1에서 백엔드를 실행합니다.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

터미널 2에서 프런트엔드를 실행합니다.

```bash
cd frontend
npm install
npm run dev
```

## 수동 실행

### Backend

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Backend URL:

- API: `http://127.0.0.1:8000`
- 상태 확인: `http://127.0.0.1:8000/api/health`
- Swagger 문서: `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

프런트엔드는 기본적으로 `http://127.0.0.1:8000`을 호출합니다. 다른 백엔드 주소를 사용할 때는 프런트엔드 환경변수 `VITE_API_URL`을 설정합니다.

## OpenAI API 설정

1. `backend/.env.example`을 `backend/.env`로 복사합니다.
2. 실제 API 키를 입력합니다.

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.4-mini
```

`backend/.env`는 Git에 포함하지 않습니다. API 키가 없거나 API 호출에 실패하면 앱은 자동으로 로컬 질문·답변 로직을 사용합니다. 상태 확인 API의 `ai` 값으로 키 인식 여부를 확인할 수 있습니다.

```json
{
  "status": "ok",
  "ai": true
}
```

## API

### 상태 확인

`GET /api/health`

### 질문 변환

`POST /api/questions/transform`

요청 예시:

```json
{
  "worry": "면접에서 계속 떨어져서 자신감이 없어졌어요.",
  "emotion": "지침",
  "mode": "stealth"
}
```

`mode`는 `stealth` 또는 `hint`만 사용할 수 있습니다. 응답에는 다섯 개의 질문, 실제 의도를 반영한 질문, AI·로컬 처리 출처가 포함됩니다.

### 부모 답변 다듬기

`POST /api/answers/polish`

요청 예시:

```json
{
  "question": "실패가 계속될 때 어떻게 다시 움직일 힘을 얻었나요?",
  "answer": "나도 처음에는 막막했지만 그냥 하루씩 버텼어."
}
```

응답에는 부모 원문, 다듬은 답변, AI·로컬 처리 출처가 포함됩니다.

## 프로젝트 구조

```text
LikeLion/
├─ backend/
│  ├─ main.py                    # FastAPI 앱 조립과 라우터 등록
│  ├─ routers/                   # 시스템·질문·답변 API
│  ├─ schemas/                   # Pydantic 요청 형식
│  ├─ services/                  # 질문 변환·답변 다듬기·OpenAI 통신
│  ├─ data/                      # 로컬 질문 은행
│  ├─ tests/                     # API 계약 및 로컬 대체 동작 테스트
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ public/
│  ├─ src/
│  │  ├─ App.jsx                 # 화면 상태와 사용자 흐름
│  │  ├─ App.css
│  │  ├─ QuestionOptions.css
│  │  └─ FeatureUpdates.css
│  ├─ package.json
│  └─ vite.config.js
├─ START.bat                     # Windows 백엔드 실행
├─ START2.bat                    # Windows 프런트엔드 실행
├─ TEAM_WORK_GUIDE.md            # 백엔드 분리 구조와 팀 작업 안내
└─ README.md
```

## 검사 명령

백엔드 계약 테스트:

```bash
cd backend
python -m unittest discover -s tests -v
```

프런트엔드 검사 및 빌드:

```bash
cd frontend
npm run lint
npm run build
```

## 다음 개발 우선순위

1. 답변 완료 후 질문·입력 상태 초기화
2. 사용자 로그인과 인증
3. 가족 생성, 초대 코드, 부모·자녀 역할 관리
4. 질문·답변 데이터베이스 저장
5. 질문의 `pending`, `viewed`, `answered` 상태 관리
6. 자녀 기기에서 부모 기기로 질문 전달
7. 답변 도착 알림과 기기 간 동기화
8. 실제 음성 인식 연결

권장 전달 흐름은 다음과 같습니다.

```text
자녀 질문 등록
  → AI 질문 변환
  → DB에 pending 상태로 저장
  → 부모가 미답변 질문 조회
  → 부모 답변 저장
  → 질문을 answered 상태로 변경
  → 자녀가 답변 확인
```

## 보안 및 개인정보

- `.env`, API 키, 가상환경, `node_modules`는 Git에 올리지 않습니다.
- 자녀가 입력한 원래 고민은 부모 화면에 그대로 노출하지 않습니다.
- 데이터베이스 도입 시 원문 고민의 저장 기간과 삭제 정책을 먼저 정해야 합니다.
- 가족과 사용자 기능을 추가할 때 모든 질문·답변 API에 가족 소속 및 역할 권한 검사를 적용해야 합니다.

## 협업

백엔드의 기능별 역할 분담과 병합 순서는 `TEAM_WORK_GUIDE.md`를 참고하세요.

커밋 메시지 예시:

```text
feat: 가족 초대 API 추가
fix: 답변 완료 후 질문 상태 초기화
docs: 현재 구현 범위와 실행법 정리
test: 질문 전달 상태 계약 테스트 추가
```
