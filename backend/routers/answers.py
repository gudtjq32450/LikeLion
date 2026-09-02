from fastapi import APIRouter

from schemas.answer import AnswerRequest
from services.answer_service import polish_answer


router = APIRouter(prefix="/api/answers", tags=["answers"])


@router.post("/polish")
def polish(body: AnswerRequest):
    return polish_answer(body)
