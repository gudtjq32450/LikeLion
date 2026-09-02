from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class QuestionRequest(BaseModel):
    worry: str = Field(..., min_length=1)
    emotion: str = Field(default="지침")
    mode: str = Field(default="stealth")

class QuestionDeliveryCreate(BaseModel):
    family_id: int
    emotion: str
    worry: str = Field(..., min_length=1)
    recipient_id: int | None = None
    mode: str = "stealth"

class QuestionDeliveryResponse(BaseModel):
    id: int
    family_id: int
    sender_id: int
    recipient_id: int | None
    emotion: str
    mode: str
    status: Literal["pending", "answered"]
    questions: list[str]
    target_question: str
    created_at: datetime
    class Config:
        from_attributes = True
