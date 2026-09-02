"""FastAPI 애플리케이션 조립 지점.

기능 구현은 routers/services/schemas에 분리되어 있습니다.
이 파일은 팀원이 새 기능을 합칠 때 라우터만 등록하도록 작게 유지합니다.
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.answers import router as answers_router
from routers.questions import router as questions_router
from routers.system import router as system_router


load_dotenv()

app = FastAPI(title="슬쩍 API", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(questions_router)
app.include_router(answers_router)
