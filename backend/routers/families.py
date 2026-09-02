from datetime import datetime, timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Family, FamilyInvite, FamilyMember, User
from schemas.family import FamilyCreateRequest, FamilyDetailResponse, FamilyInviteResponse, FamilyJoinRequest

router = APIRouter(prefix="/api/families", tags=["families"])

@router.post("", response_model=FamilyDetailResponse, status_code=status.HTTP_201_CREATED)
def create_family(body: FamilyCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    family = Family(name=body.name)
    db.add(family)
    db.flush()
    mem = FamilyMember(family_id=family.id, user_id=current_user.id, role=body.role)
    db.add(mem)
    db.commit()
    db.refresh(family)
    return {"id": family.id, "name": family.name, "members": [{"user_id": current_user.id, "name": current_user.name, "email": current_user.email, "role": body.role}], "created_at": family.created_at}

@router.post("/invites", response_model=FamilyInviteResponse)
def create_invite(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mem = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).first()
    if not mem: raise HTTPException(status_code=400, detail="가족에 소속되어 있지 않습니다.")
    code = secrets.token_hex(4).upper()
    expires_at = datetime.utcnow() + timedelta(days=3)
    invite = FamilyInvite(family_id=mem.family_id, code=code, expires_at=expires_at)
    db.add(invite)
    db.commit()
    return {"invite_code": code, "expires_at": expires_at}

@router.post("/join", response_model=FamilyDetailResponse)
def join_family(body: FamilyJoinRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    inv = db.query(FamilyInvite).filter(FamilyInvite.code == body.invite_code, FamilyInvite.expires_at > datetime.utcnow()).first()
    if not inv: raise HTTPException(status_code=404, detail="유효하지 않은 초대 코드입니다.")
    if db.query(FamilyMember).filter(FamilyMember.family_id == inv.family_id, FamilyMember.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="이미 참여한 가족입니다.")
    mem = FamilyMember(family_id=inv.family_id, user_id=current_user.id, role=body.role)
    db.add(mem)
    db.commit()
    fam = db.query(Family).filter(Family.id == inv.family_id).first()
    return {"id": fam.id, "name": fam.name, "members": [{"user_id": m.user.id, "name": m.user.name, "email": m.user.email, "role": m.role} for m in fam.members], "created_at": fam.created_at}
