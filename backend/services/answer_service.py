import re
from difflib import SequenceMatcher

from schemas.answer import AnswerRequest
from services.openai_client import request_structured_output


TONE_GUIDES = {
    "firm": ("단호하고 분명한 말투", "핵심 기준과 책임을 명확히 전달하되 모욕이나 단정은 피한다."),
    "warm": ("따뜻하고 공감하는 말투", "먼저 감정을 인정하고 가까운 관계의 온기가 느껴지게 말한다."),
    "calm": ("차분하고 설명하는 말투", "감정을 가라앉히고 이유와 경험을 순서 있게 설명한다."),
    "practical": ("현실적이고 해결 중심인 말투", "실행할 수 있는 작은 행동과 구체적인 기준에 초점을 둔다."),
    "friendly": ("친근하고 편안한 말투", "평소 대화하듯 부담 없이 솔직하고 자연스럽게 말한다."),
}

TONE_REASONS = {
    "firm": "단호한 의도는 유지하되 비난처럼 들리는 표현을 줄이면 핵심 조언을 방어적이지 않게 받아들이기 쉬워요.",
    "warm": "먼저 마음을 인정하는 표현을 더하면 가까운 관계의 온기를 지키면서 경험이 더 잘 전달될 수 있어요.",
    "calm": "감정적인 표현을 정돈하고 이유를 차분히 설명하면 답변의 뜻을 오해하지 않고 따라가기 쉬워요.",
    "practical": "조언을 작은 행동과 기준 중심으로 정리하면 부담을 덜 느끼면서 실제로 참고하기 쉬워요.",
    "friendly": "평소 대화하듯 편안하게 바꾸면 훈계받는 느낌을 줄이고 진심에 더 쉽게 다가갈 수 있어요.",
}


def normalized_text(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", text).lower()


def is_too_similar(original: str, suggestion: str) -> bool:
    source = normalized_text(original)
    revised = normalized_text(suggestion)
    if not source or not revised:
        return True
    return source in revised or SequenceMatcher(None, source, revised).ratio() >= 0.9


def ai_polish(body: AnswerRequest) -> dict | None:
    schema = {
        "type": "object",
        "properties": {
            "polished": {"type": "string"},
            "recommendation_reason": {"type": "string"},
        },
        "required": ["polished", "recommendation_reason"],
        "additionalProperties": False,
    }
    tone_name, tone_guide = TONE_GUIDES[body.tone]
    instructions = (
        "당신은 부모가 말한 답변을 가족에게 전하기 좋은 한국어 문장으로 완전히 다시 쓰는 편집자다. "
        "질문에 직접 답하고, 원문에 없는 사건·감정·행동·교훈은 만들지 않는다. 원문의 사실과 개성은 보존하되 "
        "원문 문장을 그대로 감싸지 말고 선택한 문체로 자연스러운 하나의 답변을 만든다. 맞춤법, 띄어쓰기, 조사, "
        "어미, 문장부호도 교정한다. 가벼운 질문은 밝고 자연스러운 1~2문장, 깊은 질문은 원문 범위 안에서 2~4문장으로 쓴다. "
        "답변자는 부모이며 1인칭 회고 말투를 사용한다. 질문을 반복하거나 서론을 붙이지 않는다. "
        f"선택 문체는 '{tone_name}'이다. {tone_guide} recommendation_reason에는 무엇을 어떻게 개선했고 왜 전달에 도움이 되는지 1~2문장으로 설명한다."
    )
    parsed = request_structured_output(
        instructions=instructions,
        input_text=f"질문: {body.question}\n선택 문체: {tone_name}\n부모의 원문 답변: {body.answer}",
        schema_name="polished_parent_answer",
        schema=schema,
    )
    if not parsed:
        return None
    polished = parsed.get("polished")
    reason = parsed.get("recommendation_reason")
    if not polished or not reason or is_too_similar(body.answer, polished):
        return None
    return {
        "polished": polished.strip(),
        "recommendation_reason": reason.strip(),
        "source": parsed.get("_provider", "ai"),
    }


def rewrite_local_core(text: str) -> str:
    revised = re.sub(r"\s+", " ", text).strip().rstrip(".!? ")
    replacements = {
        "그렇게 하면 안 돼": "그 방법은 다시 한번 생각해 볼 필요가 있어",
        "정신 차리고": "마음을 가다듬고",
        "제대로 해": "차근차근 해 나가면 좋겠어",
        "왜 그것도 못해": "잘되지 않는 부분부터 함께 살펴보자",
        "네가 문제야": "지금 겪는 어려움부터 돌아볼 필요가 있어",
        "무조건": "가능하면",
        "그냥 버텨": "하루씩 견뎌 보자",
        "하지 마": "피하면 좋겠어",
        "해야 돼": "해보는 게 좋겠어",
    }
    for source, target in replacements.items():
        revised = revised.replace(source, target)
    revised = re.sub(r"^(나는|나도)\s+", "돌이켜보면 나는 ", revised)
    revised = re.sub(r"했어$", "했단다", revised)
    revised = re.sub(r"였어$", "였단다", revised)
    revised = re.sub(r"했지$", "했단다", revised)
    revised = re.sub(r"거야$", "것이란다", revised)
    revised = re.sub(r"돼$", "하는 게 좋겠어", revised)
    revised = re.sub(r"힘들어$", "힘든 순간이 있었단다", revised)
    if normalized_text(text) in normalized_text(revised):
        words = revised.split(" ", 1)
        revised = f"내 경험을 돌아보면, {words[0]}에 대해서는 {words[1]}" if len(words) == 2 else "그때의 마음과 상황을 조금 더 차분히 돌아볼 필요가 있단다"
    return revised


def polish_local(text: str, question: str, tone: str) -> str:
    text = rewrite_local_core(text)
    light_markers = ("음식", "간식", "노래", "취미", "여행", "학창", "웃", "계절", "월급", "닮", "쉬는 날")
    if any(marker in question for marker in light_markers):
        base = f"{text.rstrip('. ')}."
        if tone == "friendly":
            return f"{base} 생각만 해도 웃음이 나네."
        if tone == "calm":
            return f"돌이켜보면 {base}"
        return base
    replacements = {
        "그냥 버텼": "하루씩 견뎌냈",
        "별거 아니": "지나고 보니 그 시간도 삶의 한 부분이었",
        "다 쓸모가 있": "모두 다음 길을 알아보는 힘이 되어 주었",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    if len(text) < 28 and tone != "firm":
        text = f"나도 처음에는 쉽지 않았단다. {text}"
    endings = {
        "firm": "중요한 건 피하지 않고 네가 선택한 일에 책임을 다하는 거야.",
        "warm": "지금은 앞이 보이지 않더라도 네 마음을 이해하고 늘 곁에서 응원할게.",
        "calm": "서두르지 말고 상황을 하나씩 살펴보면 다음 길을 찾을 수 있을 거야.",
        "practical": "우선 오늘 할 수 있는 가장 작은 일부터 하나 정해 보면 좋겠어.",
        "friendly": "너무 혼자 끙끙대지 말고 편할 때 같이 이야기해 보자.",
    }
    return f"{text}. {endings[tone]}"


def polish_answer(body: AnswerRequest) -> dict:
    suggestion = ai_polish(body)
    return {
        "polished": suggestion["polished"] if suggestion else polish_local(body.answer, body.question, body.tone),
        "recommendation_reason": suggestion["recommendation_reason"] if suggestion else f"{TONE_REASONS[body.tone]} 맞춤법과 문장 호응도 함께 자연스럽게 정리했어요.",
        "original": body.answer,
        "tone": body.tone,
        "source": suggestion["source"] if suggestion else "local",
    }
