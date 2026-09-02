from typing import Literal

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    worry: str = Field(min_length=1, max_length=500)
    emotion: str = Field(default="지침", max_length=30)
    mode: Literal["stealth", "hint"] = "stealth"
