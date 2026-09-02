import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Answer, FamilyMember, QuestionDelivery, Reaction, User
from schemas.answer import AnswerCreateRequest, AnswerRequest, AnswerResponse, ReactionRequest
from services.answer_service import polish_answer

router = APIRouter(prefix="/api/answers", tags=["answers"])

@router.post("/polish")
def polish(body: AnswerRequest):
    return polish_answer(body)

@router.post("/deliveries/{delivery_id}", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
def submit_answer(delivery_id: int, body: AnswerCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    delivery = db.query(QuestionDelivery).filter(QuestionDelivery.id == delivery_id).first()
    if not delivery: raise HTTPException(status_code=404, detail="질문이 없습니다.")
    mem = db.query(FamilyMember).filter(FamilyMember.family_id == delivery.family_id, FamilyMember.user_id == current_user.id).first()
    if not mem or mem.role != "parent": raise HTTPException(status_code=403, detail="부모 권한만 답변 가능합니다.")
    if delivery.status == "answered": raise HTTPException(status_code=400, detail="이미 답변된 질문입니다.")
    if body.question not in json.loads(delivery.questions_bundle):
        raise HTTPException(status_code=400, detail="전달된 질문 중 하나를 선택해 주세요.")
    polished_res = polish_answer(AnswerRequest(answer=body.answer, question=body.question))
    answer = Answer(delivery_id=delivery.id, respondent_id=current_user.id, question=body.question, raw_answer=body.answer, polished_answer=polished_res["polished"])
    db.add(answer)
    delivery.status = "answered"
    db.commit()
    db.refresh(answer)
    return {"id": answer.id, "delivery_id": answer.delivery_id, "respondent_id": answer.respondent_id, "author_name": current_user.name, "emotion": delivery.emotion, "question": answer.question, "raw_answer": answer.raw_answer, "polished_answer": answer.polished_answer, "thanks_count": 0, "moved_count": 0, "created_at": answer.created_at}

@router.get("", response_model=list[AnswerResponse])
def get_library_answers(family_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="조회 권한이 없습니다.")
    answers = db.query(Answer).join(QuestionDelivery, Answer.delivery_id == QuestionDelivery.id).filter(QuestionDelivery.family_id == family_id).order_by(Answer.created_at.desc()).all()
    res = []
    for a in answers:
        u = db.query(User).filter(User.id == a.respondent_id).first()
        tc = db.query(Reaction).filter(Reaction.answer_id == a.id, Reaction.reaction_type == "thanks").count()
        mc = db.query(Reaction).filter(Reaction.answer_id == a.id, Reaction.reaction_type == "moved").count()
        res.append({"id": a.id, "delivery_id": a.delivery_id, "respondent_id": a.respondent_id, "author_name": u.name if u else "부모님", "emotion": a.delivery.emotion if a.delivery else None, "question": a.question, "raw_answer": a.raw_answer, "polished_answer": a.polished_answer, "thanks_count": tc, "moved_count": mc, "created_at": a.created_at})
    return res

@router.post("/{answer_id}/reactions")
def react_answer(answer_id: int, body: ReactionRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="답변을 찾을 수 없습니다.")
    membership = db.query(FamilyMember).filter(
        FamilyMember.family_id == answer.delivery.family_id,
        FamilyMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="반응을 남길 권한이 없습니다.")
    reaction = Reaction(answer_id=answer_id, user_id=current_user.id, reaction_type=body.reaction_type)
    db.add(reaction)
    db.commit()
    return {"message": "반응 완료"}
