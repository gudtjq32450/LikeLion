import re

from schemas.answer import AnswerRequest
from services.openai_client import request_structured_output


def ai_polish(body: AnswerRequest) -> str | None:
    schema = {
        "type": "object",
        "properties": {"polished": {"type": "string"}},
        "required": ["polished"],
        "additionalProperties": False,
    }
    instructions = (
        "당신은 부모가 말한 답변을 가족에게 전하기 좋은 한국어 문장으로 다듬는 편집자다. 먼저 질문이 정확히 무엇을 묻는지 파악하고, 다듬은 답변이 "
        "그 질문에 직접 답하도록 한다. 부모가 말하지 않은 사건, 감정, 행동, 교훈은 절대 새로 만들지 않는다. 원문의 구체적인 사실과 말투의 개성은 보존하되 "
        "명령, 비난, 잔소리처럼 들리는 부분만 부드럽게 바꾼다. 음식·취미·여행·학창 시절 같은 가벼운 질문에는 인생 교훈이나 과한 위로를 붙이지 말고 "
        "밝고 자연스러운 1~2문장으로 쓴다. 실패·불안·관계 같은 깊은 질문에는 경험, 당시 마음, 도움이 된 행동이 원문에 있는 범위에서 드러나도록 2~4문장으로 쓴다. "
        "답변자는 부모이므로 1인칭 회고 말투를 사용하고, 자녀가 읽는다는 사실을 노골적으로 드러내지 않는다. 질문을 반복하거나 서론을 붙이지 않는다."
    )
    parsed = request_structured_output(
        instructions=instructions,
        input_text=f"질문: {body.question}\n부모의 원문 답변: {body.answer}",
        schema_name="polished_parent_answer",
        schema=schema,
    )
    if not parsed:
        return None

    polished = parsed.get("polished")
    return polished.strip() if polished else None


def polish_local(text: str, question: str) -> str:
    text = re.sub(r"\s+", " ", text).strip().rstrip(". ")
    light_markers = (
        "음식", "간식", "노래", "취미", "여행", "학창", "웃", "계절",
        "월급", "닮", "쉬는 날",
    )
    if any(marker in question for marker in light_markers):
        return f"{text}."

    replacements = {
        "그냥 버텼": "하루씩 견뎌냈",
        "별거 아니": "지나고 보니 그 시간도 삶의 한 부분이었",
        "다 쓸모가 있": "모두 다음 길을 알아보는 힘이 되어 주었",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    if len(text) < 28:
        text = f"나도 처음에는 쉽지 않았단다. {text}"
    return f"{text}. 지금은 앞이 보이지 않더라도, 네가 지나온 시간은 사라지지 않고 분명 다음 걸음을 내딛는 힘이 되어 줄 거야."


def polish_answer(body: AnswerRequest) -> dict:
    polished = ai_polish(body)
    source = "openai" if polished else "local"
    return {
        "polished": polished or polish_local(body.answer, body.question),
        "original": body.answer,
        "source": source,
    }
