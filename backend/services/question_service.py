import random
import re

from data.question_bank import (
    GENERAL_QUESTIONS,
    LIGHT_KEYWORDS,
    LIGHT_QUESTIONS,
    LIGHT_TARGET_RULES,
    QUESTION_POOLS,
)
from schemas.question import QuestionRequest
from services.openai_client import request_structured_output


def local_question_feed(text: str, emotion: str) -> dict:
    normalized = re.sub(r"\s+", " ", text).lower()
    ranked = []
    for pool in QUESTION_POOLS.values():
        score = sum(1 for keyword in pool["keywords"] if keyword in normalized)
        if score:
            ranked.append((score, pool["questions"]))
    ranked.sort(key=lambda item: item[0], reverse=True)

    seed = sum(ord(char) for char in normalized + emotion)
    rng = random.Random(seed)
    is_light = any(keyword in normalized for keyword in LIGHT_KEYWORDS)
    target_pool = LIGHT_QUESTIONS if is_light else (ranked[0][1] if ranked else GENERAL_QUESTIONS)
    target = rng.choice(target_pool)

    if is_light:
        for keywords, tailored_question in LIGHT_TARGET_RULES:
            if any(keyword in normalized for keyword in keywords):
                target = tailored_question
                break

    decoy_pools = [
        pool["questions"]
        for pool in QUESTION_POOLS.values()
        if pool["questions"] is not target_pool
    ]
    rng.shuffle(decoy_pools)
    light_decoys = [question for question in LIGHT_QUESTIONS if question != target]
    rng.shuffle(light_decoys)
    decoys = light_decoys[:2]
    decoys.append(rng.choice(decoy_pools[0]))
    decoys.append(rng.choice([question for question in GENERAL_QUESTIONS if question != target]))

    feed = list(dict.fromkeys([target, *decoys]))
    while len(feed) < 5:
        candidate = rng.choice(GENERAL_QUESTIONS)
        if candidate not in feed:
            feed.append(candidate)
    rng.shuffle(feed)
    return {"target_question": target, "feed": feed}


def ai_question_feed(body: QuestionRequest) -> dict | None:
    schema = {
        "type": "object",
        "properties": {
            "target_question": {"type": "string"},
            "decoy_questions": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {"type": "string"},
            },
        },
        "required": ["target_question", "decoy_questions"],
        "additionalProperties": False,
    }
    instructions = (
        "당신은 자녀의 말 못 할 고민을 부모에게 들키지 않게 전달하는 한국어 질문 편집자다. target_question 한 개에는 자녀가 실제로 알고 싶은 "
        "핵심 정보와 질문 의도(무엇을 겪었는지, 어떻게 견뎠는지, 어떤 기준이었는지 등)를 반드시 보존한다. 다만 자녀, 현재 사건, 회사명, 시험명, 인물 등 "
        "신원을 짐작할 단서는 지우고 부모 자신의 과거 경험을 묻는 자연스러운 회고 질문으로 바꾼다. 지나치게 보편화해 핵심 의도를 잃지 않는다. "
        "decoy_questions 네 개는 target과 무관한 일상, 추억, 관계, 가치관 주제를 서로 다르게 만든다. 다섯 질문은 문체와 길이가 비슷해야 하며 어느 것이 "
        "자녀 질문인지 구별할 수 없어야 한다. 모두 35~65자의 존댓말 한 문장으로 작성하고 조언을 직접 요구하지 않는다."
        "자녀 질문 자체가 가벼운 취향이나 추억 질문이면 의미를 과장하거나 무겁게 만들지 않는다. decoy_questions 중 최소 두 개는 음식, 취미, 학창 시절, "
        "여행, 계절, 소소한 웃음처럼 짧게 답해도 즐거운 가벼운 질문으로 만들고, 다섯 질문 전체가 상담 설문처럼 느껴지지 않게 질문의 무게를 섞는다."
    )
    parsed = request_structured_output(
        instructions=instructions,
        input_text=f"자녀 감정: {body.emotion}\n전달 모드: {body.mode}\n자녀 고민: {body.worry}",
        schema_name="family_questions",
        schema=schema,
    )
    if not parsed:
        return None

    target = parsed.get("target_question")
    decoys = parsed.get("decoy_questions", [])
    if not target or len(decoys) != 4:
        return None

    feed = [target, *decoys]
    random.SystemRandom().shuffle(feed)
    return {"target_question": target, "feed": feed, "source": parsed.get("_provider", "ai")}


def transform_question(body: QuestionRequest) -> dict:
    result = ai_question_feed(body)
    source = result.get("source", "ai") if result else "local"
    result = result or local_question_feed(body.worry, body.emotion)
    questions = [result["target_question"]] if body.mode == "direct" else result["feed"]
    return {
        "question": questions[0],
        "questions": questions,
        "target_question": result["target_question"],
        "source": source,
        "mode": body.mode,
        "emotion": body.emotion,
        "privacy": (
            "자녀 질문 한 개가 네 개의 일상 질문 사이에 익명으로 섞였습니다."
            if body.mode == "stealth"
            else "자녀의 고민을 익명화한 회고 질문 한 개로 전달합니다."
        ),
    }
