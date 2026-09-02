import json
import os
import random
import re
import urllib.error
import urllib.request
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()
app = FastAPI(title="슬쩍 API", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class QuestionRequest(BaseModel):
    worry: str = Field(min_length=1, max_length=500)
    emotion: str = Field(default="지침", max_length=30)
    mode: Literal["stealth", "hint"] = "stealth"


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=2000)
    question: str = Field(default="", max_length=500)


QUESTION_POOLS = {
    "career": {
        "keywords": ("면접", "취업", "탈락", "회사", "직장", "이직", "시험", "합격"),
        "questions": [
            "청년 시절, 가장 포기하고 싶었던 순간과 그것을 이겨낸 계기는 무엇인가요?",
            "노력해도 결과가 따라오지 않을 때, 마음을 다시 일으킨 방법은 무엇이었나요?",
            "처음 사회에 나설 때 가장 막막했던 일과, 지금의 나에게 해주고 싶은 말은 무엇인가요?",
            "기회가 계속 멀어지는 것처럼 느껴졌을 때, 어떤 작은 행동을 이어갔나요?",
            "실패라고 생각했던 경험이 나중에 다른 길을 열어 준 적이 있나요?",
        ],
    },
    "failure": {
        "keywords": ("실패", "망했", "포기", "못하", "후회", "좌절", "자신감"),
        "questions": [
            "뜻대로 되지 않아 실패했다고 느꼈을 때, 다시 일어설 수 있었던 힘은 무엇이었나요?",
            "스스로가 작아 보였던 시절, 다시 자신을 믿게 된 계기가 있었나요?",
            "돌이켜보면 실패가 아니라 방향을 바꾼 순간이었던 경험이 있나요?",
            "큰 후회를 품고도 하루를 살아가기 위해 했던 가장 작은 일은 무엇이었나요?",
        ],
    },
    "relationship": {
        "keywords": ("친구", "연애", "헤어", "관계", "싸웠", "사람", "부모", "가족"),
        "questions": [
            "소중한 사람과 마음이 멀어졌을 때, 관계를 다시 이어 본 경험이 있나요?",
            "사람에게 상처받았을 때도 마음을 닫지 않을 수 있었던 이유는 무엇인가요?",
            "오래된 관계를 지키기 위해 먼저 내려놓아야 했던 것은 무엇이었나요?",
            "이별 뒤에야 알게 된 사랑이나 관계의 의미가 있었나요?",
        ],
    },
    "choice": {
        "keywords": ("진로", "꿈", "선택", "전공", "결정", "앞날", "미래"),
        "questions": [
            "인생의 갈림길에서 어떤 기준으로 나만의 길을 선택했나요?",
            "남들이 원하는 길과 내가 원하는 길이 달랐을 때 어떻게 결정했나요?",
            "정답이 없는 선택 앞에서 후회를 줄이기 위해 무엇을 확인했나요?",
            "계획과 다른 길을 걷게 되었지만 오히려 잘됐다고 느낀 적이 있나요?",
        ],
    },
    "money": {
        "keywords": ("돈", "월급", "경제", "생활비", "빚", "집", "가난"),
        "questions": [
            "형편이 넉넉하지 않았던 시절, 마음을 지키며 살아낸 방법은 무엇이었나요?",
            "돈 때문에 중요한 선택을 망설였을 때 무엇을 우선순위에 두었나요?",
            "적은 것으로도 충분하다고 느꼈던 기억이 있나요?",
            "경제적으로 가장 불안했던 때, 생활을 다시 세운 첫걸음은 무엇이었나요?",
        ],
    },
    "lonely": {
        "keywords": ("외로", "혼자", "쓸쓸", "우울", "힘들", "지쳐", "불안"),
        "questions": [
            "혼자라고 느꼈던 시절, 곁을 지켜 준 말이나 기억이 있었나요?",
            "아무것도 하고 싶지 않을 만큼 지쳤을 때, 하루를 건너게 해 준 것은 무엇이었나요?",
            "걱정이 꼬리를 물던 밤, 마음을 조금 편하게 해 준 방법이 있었나요?",
            "누군가에게 약한 모습을 보여도 괜찮다고 처음 느낀 순간은 언제였나요?",
        ],
    },
}

GENERAL_QUESTIONS = [
    "살면서 마음처럼 되지 않았지만, 결국 나를 단단하게 만든 순간은 언제였나요?",
    "지금의 나를 만든, 그때는 미처 몰랐던 중요한 경험이 있나요?",
    "힘든 시절의 나에게 한 문장만 건넬 수 있다면 어떤 말을 해주고 싶나요?",
    "인생에서 서두르지 않아도 된다는 걸 깨달은 순간이 있었나요?",
    "누군가의 짧은 말이 오래 힘이 되어 준 경험이 있나요?",
    "돌아보면 잘 견뎌냈다고 스스로를 안아주고 싶은 때는 언제인가요?",
]

LIGHT_KEYWORDS = ("좋아", "먹", "음식", "노래", "영화", "여행", "취미", "주말", "어릴 때", "학교", "친구랑", "재미", "행복")
LIGHT_QUESTIONS = [
    "어릴 때 용돈을 받으면 가장 먼저 사고 싶었던 것은 무엇인가요?",
    "요즘 다시 먹고 싶은 어린 시절의 간식이 있나요?",
    "학창 시절 친구들과 가장 많이 웃었던 기억은 무엇인가요?",
    "하루를 쉬게 된다면 아무 계획 없이 가장 하고 싶은 일은 무엇인가요?",
    "처음 혼자 떠났던 여행에서 가장 기억에 남는 장면은 무엇인가요?",
    "기분이 좋아질 때 무심코 흥얼거리는 노래가 있나요?",
    "가족과 다시 한번 함께 먹고 싶은 음식은 무엇인가요?",
    "어릴 때는 좋아했지만 지금은 잊고 지낸 취미가 있나요?",
    "최근 예상하지 못하게 웃음이 났던 순간은 언제였나요?",
    "계절이 바뀔 때마다 떠오르는 가족의 추억이 있나요?",
    "지금도 또렷하게 기억나는 첫 월급날의 작은 소비가 있나요?",
    "우리 가족 중 나와 가장 닮았다고 느끼는 사람은 누구인가요?",
]
LIGHT_TARGET_RULES = [
    (("먹", "음식", "간식", "요리"), "어릴 때 가장 좋아해서 자주 찾았던 음식이나 간식은 무엇인가요?"),
    (("노래", "음악", "가수"), "젊은 시절 가장 좋아해서 자주 들었던 노래는 무엇인가요?"),
    (("여행", "놀러", "휴가"), "지금도 다시 가보고 싶은 가장 즐거웠던 여행지는 어디인가요?"),
    (("취미", "주말", "쉬는 날"), "시간 가는 줄 모르고 즐겼던 취미나 주말 활동이 있었나요?"),
    (("학교", "학창", "친구"), "학창 시절 친구들과 가장 많이 웃었던 기억은 무엇인가요?"),
]


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
    decoy_pools = [pool["questions"] for pool in QUESTION_POOLS.values() if pool["questions"] is not target_pool]
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    schema = {
        "type": "object",
        "properties": {
            "target_question": {"type": "string"},
            "decoy_questions": {"type": "array", "minItems": 4, "maxItems": 4, "items": {"type": "string"}},
        },
        "required": ["target_question", "decoy_questions"],
        "additionalProperties": False,
    }
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        "store": False,
        "instructions": (
            "당신은 자녀의 말 못 할 고민을 부모에게 들키지 않게 전달하는 한국어 질문 편집자다. target_question 한 개에는 자녀가 실제로 알고 싶은 "
            "핵심 정보와 질문 의도(무엇을 겪었는지, 어떻게 견뎠는지, 어떤 기준이었는지 등)를 반드시 보존한다. 다만 자녀, 현재 사건, 회사명, 시험명, 인물 등 "
            "신원을 짐작할 단서는 지우고 부모 자신의 과거 경험을 묻는 자연스러운 회고 질문으로 바꾼다. 지나치게 보편화해 핵심 의도를 잃지 않는다. "
            "decoy_questions 네 개는 target과 무관한 일상, 추억, 관계, 가치관 주제를 서로 다르게 만든다. 다섯 질문은 문체와 길이가 비슷해야 하며 어느 것이 "
            "자녀 질문인지 구별할 수 없어야 한다. 모두 35~65자의 존댓말 한 문장으로 작성하고 조언을 직접 요구하지 않는다."
            "자녀 질문 자체가 가벼운 취향이나 추억 질문이면 의미를 과장하거나 무겁게 만들지 않는다. decoy_questions 중 최소 두 개는 음식, 취미, 학창 시절, "
            "여행, 계절, 소소한 웃음처럼 짧게 답해도 즐거운 가벼운 질문으로 만들고, 다섯 질문 전체가 상담 설문처럼 느껴지지 않게 질문의 무게를 섞는다."
        ),
        "input": f"자녀 감정: {body.emotion}\n전달 모드: {body.mode}\n자녀 고민: {body.worry}",
        "text": {"format": {"type": "json_schema", "name": "family_questions", "strict": True, "schema": schema}},
        "max_output_tokens": 500,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
        output_text = result.get("output_text")
        if not output_text:
            for item in result.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        output_text = content.get("text")
                        break
        parsed = json.loads(output_text or "{}")
        target = parsed.get("target_question")
        decoys = parsed.get("decoy_questions", [])
        if not target or len(decoys) != 4:
            return None
        feed = [target, *decoys]
        random.SystemRandom().shuffle(feed)
        return {"target_question": target, "feed": feed}
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
        return None


def ai_polish(body: AnswerRequest) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    schema = {
        "type": "object",
        "properties": {"polished": {"type": "string"}},
        "required": ["polished"],
        "additionalProperties": False,
    }
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        "store": False,
        "instructions": (
            "당신은 부모가 말한 답변을 가족에게 전하기 좋은 한국어 문장으로 다듬는 편집자다. 먼저 질문이 정확히 무엇을 묻는지 파악하고, 다듬은 답변이 "
            "그 질문에 직접 답하도록 한다. 부모가 말하지 않은 사건, 감정, 행동, 교훈은 절대 새로 만들지 않는다. 원문의 구체적인 사실과 말투의 개성은 보존하되 "
            "명령, 비난, 잔소리처럼 들리는 부분만 부드럽게 바꾼다. 음식·취미·여행·학창 시절 같은 가벼운 질문에는 인생 교훈이나 과한 위로를 붙이지 말고 "
            "밝고 자연스러운 1~2문장으로 쓴다. 실패·불안·관계 같은 깊은 질문에는 경험, 당시 마음, 도움이 된 행동이 원문에 있는 범위에서 드러나도록 2~4문장으로 쓴다. "
            "답변자는 부모이므로 1인칭 회고 말투를 사용하고, 자녀가 읽는다는 사실을 노골적으로 드러내지 않는다. 질문을 반복하거나 서론을 붙이지 않는다."
        ),
        "input": f"질문: {body.question}\n부모의 원문 답변: {body.answer}",
        "text": {"format": {"type": "json_schema", "name": "polished_parent_answer", "strict": True, "schema": schema}},
        "max_output_tokens": 500,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
        output_text = result.get("output_text")
        if not output_text:
            for item in result.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        output_text = content.get("text")
                        break
        polished = json.loads(output_text or "{}").get("polished")
        return polished.strip() if polished else None
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
        return None


def polish_local(text: str, question: str) -> str:
    text = re.sub(r"\s+", " ", text).strip().rstrip(". ")
    light_markers = ("음식", "간식", "노래", "취미", "여행", "학창", "웃", "계절", "월급", "닮", "쉬는 날")
    if any(marker in question for marker in light_markers):
        return f"{text}."
    replacements = {"그냥 버텼": "하루씩 견뎌냈", "별거 아니": "지나고 보니 그 시간도 삶의 한 부분이었", "다 쓸모가 있": "모두 다음 길을 알아보는 힘이 되어 주었"}
    for source, target in replacements.items():
        text = text.replace(source, target)
    if len(text) < 28:
        text = f"나도 처음에는 쉽지 않았단다. {text}"
    return f"{text}. 지금은 앞이 보이지 않더라도, 네가 지나온 시간은 사라지지 않고 분명 다음 걸음을 내딛는 힘이 되어 줄 거야."


@app.get("/")
def root():
    return {"message": "슬쩍 API가 마음을 잇고 있어요."}


@app.get("/api/health")
def health():
    return {"status": "ok", "ai": bool(os.getenv("OPENAI_API_KEY"))}


@app.post("/api/questions/transform")
def transform(body: QuestionRequest):
    result = ai_question_feed(body)
    source = "openai" if result else "local"
    result = result or local_question_feed(body.worry, body.emotion)
    return {
        "question": result["feed"][0],
        "questions": result["feed"],
        "target_question": result["target_question"],
        "source": source,
        "mode": body.mode,
        "emotion": body.emotion,
        "privacy": "자녀 질문 한 개가 네 개의 일상 질문 사이에 익명으로 섞였습니다.",
    }


@app.post("/api/answers/polish")
def polish(body: AnswerRequest):
    polished = ai_polish(body)
    source = "openai" if polished else "local"
    return {"polished": polished or polish_local(body.answer, body.question), "original": body.answer, "source": source}
