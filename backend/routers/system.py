import os

from fastapi import APIRouter


router = APIRouter(tags=["system"])


@router.get("/")
def root():
    return {"message": "슬쩍 API가 마음을 잇고 있어요."}


@router.get("/api/health")
def health():
    return {"status": "ok", "ai": bool(os.getenv("OPENAI_API_KEY"))}
