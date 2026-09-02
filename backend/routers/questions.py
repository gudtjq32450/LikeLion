import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import FamilyMember, QuestionDelivery, User
from schemas.question import QuestionDeliveryCreate, QuestionDeliveryResponse, QuestionRequest
from services.question_service import transform_question

router = APIRouter(prefix="/api/questions", tags=["questions"])

@router.post("/transform")
def transform(body: QuestionRequest):
    return transform_question(body)

@router.post("/deliveries", response_model=QuestionDeliveryResponse, status_code=status.HTTP_201_CREATED)
def create_question_delivery(body: QuestionDeliveryCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mem = db.query(FamilyMember).filter(FamilyMember.family_id == body.family_id, FamilyMember.user_id == current_user.id).first()
    if not mem: raise HTTPException(status_code=403, detail="가족 구성원이 아닙니다.")
    if body.recipient_id is not None:
        recipient = db.query(FamilyMember).filter(
            FamilyMember.family_id == body.family_id,
            FamilyMember.user_id == body.recipient_id,
            FamilyMember.role == "parent",
        ).first()
        if not recipient:
            raise HTTPException(status_code=400, detail="수신자는 해당 가족의 부모 구성원이어야 합니다.")
    req = QuestionRequest(worry=body.worry, emotion=body.emotion, mode=body.mode)
    res = transform_question(req)
    delivery = QuestionDelivery(
        family_id=body.family_id, sender_id=current_user.id, recipient_id=body.recipient_id,
        emotion=body.emotion, mode=body.mode, target_question=res["target_question"],
        questions_bundle=json.dumps(res["questions"], ensure_ascii=False), status="pending"
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return {"id": delivery.id, "family_id": delivery.family_id, "sender_id": delivery.sender_id, "recipient_id": delivery.recipient_id, "emotion": delivery.emotion, "mode": delivery.mode, "status": delivery.status, "questions": json.loads(delivery.questions_bundle), "target_question": delivery.target_question, "created_at": delivery.created_at}

@router.get("/deliveries", response_model=list[QuestionDeliveryResponse])
def get_question_deliveries(family_id: int, status: str = Query("pending"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mem = db.query(FamilyMember).filter(FamilyMember.family_id == family_id, FamilyMember.user_id == current_user.id).first()
    if not mem: raise HTTPException(status_code=403, detail="조회 권한이 없습니다.")
    if status not in {"pending", "answered", "all"}:
        raise HTTPException(status_code=400, detail="status는 pending, answered 또는 all이어야 합니다.")
    query = db.query(QuestionDelivery).filter(QuestionDelivery.family_id == family_id)
    if mem.role == "parent":
        query = query.filter((QuestionDelivery.recipient_id == current_user.id) | (QuestionDelivery.recipient_id.is_(None)))
    if status != "all":
        query = query.filter(QuestionDelivery.status == status)
    deliveries = query.order_by(QuestionDelivery.created_at.desc()).all()
    return [{"id": d.id, "family_id": d.family_id, "sender_id": d.sender_id, "recipient_id": d.recipient_id, "emotion": d.emotion, "mode": d.mode, "status": d.status, "questions": json.loads(d.questions_bundle), "target_question": d.target_question, "created_at": d.created_at} for d in deliveries]
