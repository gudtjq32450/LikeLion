import re
from difflib import SequenceMatcher

from schemas.answer import AnswerRequest
from services.openai_client import request_structured_output


TONE_GUIDES = {
    "warm": (
        "따뜻하고 공감되게",
        "상대의 힘든 감정을 먼저 인정하면서 부모의 응원과 믿음을 전달한다. 감정을 무시하지 않고 공격적 표현은 완전 제거하되, 지나치게 감상적이거나 원문에 없는 감정을 지어내지 않는다.",
    ),
    "firm": (
        "단호하고 분명하게",
        "부모가 전달하고 싶은 기준과 메시지를 분명하게 전달한다. 단호함과 공격성을 구분하여 욕설, 비하, 조롱 없이 핵심 행동이나 기준을 명확하게 제시한다.",
    ),
    "calm": (
        "차분하게 설명하기",
        "감정적인 표현을 제거하고 왜 그런 조언을 하는지 이해할 수 있게 설명한다. 원문의 논리를 자연스러운 인과관계로 정리하고 공격적 명령 대신 생각의 이유를 전달한다.",
    ),
    "practical": (
        "현실적인 해결 중심",
        "원문의 조언을 실제 행동으로 옮길 수 있게 만든다. 지나친 방법론 창작 없이, 지금 바로 실행할 수 있는 가장 작은 행동 단위로 구체화한다.",
    ),
    "friendly": (
        "친근하고 편안하게",
        "부모 특유의 솔직함과 에너지는 살리면서 공격성은 완전히 제거한다. 너무 교과서적이지 않은 적절한 구어체를 사용하되 욕설이나 비하는 배제한다.",
    ),
}

TONE_REASONS = {
    "warm": "상대의 지친 마음을 먼저 헤아리면서도 전하고자 하는 핵심 응원과 믿음이 온전히 전해지도록 다듬었어요.",
    "firm": "감정적인 표현이나 비난을 걷어내고, 꼭 전달하고 싶은 기준과 책임을 흐려지지 않게 분명히 세웠어요.",
    "calm": "격앙된 어조를 가라앉히고, 왜 그런 생각을 전하는지 이유를 순서 있게 설명하여 받아들이기 편하게 했어요.",
    "practical": "막연하거나 거친 명령 대신, 자녀가 오늘 당장 시도해 볼 수 있는 작은 행동 단위로 바꿨어요.",
    "friendly": "훈계나 잔소리처럼 들리지 않도록 평소 나누는 대화처럼 편안하고 솔직한 구어체로 정리했어요.",
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
    tone_name, tone_guide = TONE_GUIDES.get(body.tone, TONE_GUIDES["warm"])
    instructions = (
        "당신은 부모가 즉흥적으로 말한 거칠고 투박한 답변에서 진짜 전달 의도와 가치관을 추출하여, "
        "자녀에게 자연스럽고 도움이 되는 한국어 문장으로 다시 표현하는 가족 대화 전문 에디터입니다.\n\n"
        "[핵심 원칙]\n"
        "1. 원문의 단어를 단순히 순화하거나 문법만 고치는 것이 아닙니다. "
        "욕설, 비속어, 모욕, 비난, 조롱, 위협적 표현, 공격적인 명령은 보존 대상이 아닙니다. "
        "그 표현 뒤에 있는 화자의 핵심 의도, 주장, 가치관, 태도만 추출하여 새로운 문장으로 재구성하세요. "
        "원문의 비속어나 공격적인 어구의 흔적을 절대로 남겨서는 안 됩니다.\n"
        "2. 질문 의도 파악: 자녀가 한 질문의 맥락과 연결하여 답변을 구성하세요.\n"
        "3. 사실 날조 금지: 원문에 없는 부모의 구체적 과거 사건(사업 실패, 특정 경험 등)을 사실처럼 지어내지 마세요. 다만 기존 조언의 현실적 의미를 자연스럽게 설명하는 확장은 권장됩니다.\n"
        "4. 화자 정체성: 답변자는 부모이며 1인칭 회고 및 대화 말투를 사용합니다. 서론('질문에 답하자면...' 등) 없이 본론으로 시작하세요.\n"
        f"5. 선택된 문체 목표: '{tone_name}' - {tone_guide}\n"
        "6. recommendation_reason: 무엇을 어떻게 개선했고 왜 자녀와의 대화에 도움이 되는지 1~2문장으로 친절하게 설명하세요."
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
