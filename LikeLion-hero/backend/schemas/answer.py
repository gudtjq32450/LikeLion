from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=2000)
    question: str = Field(default="", max_length=500)
