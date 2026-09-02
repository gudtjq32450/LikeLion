import os
from fastapi import APIRouter

router = APIRouter(tags=["system"])

@router.get("/")
def root(): return {"message": "슬쩍 API가 마음을 잇고 있어요."}

@router.get("/api/health")
def health():
    gk = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    ok = bool(os.getenv("OPENAI_API_KEY"))
    return {"status": "ok", "ai": gk or ok, "provider": "gemini" if gk else ("openai" if ok else "local")}
