from fastapi import APIRouter

from schemas.question import QuestionRequest
from services.question_service import transform_question


router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.post("/transform")
def transform(body: QuestionRequest):
    return transform_question(body)
