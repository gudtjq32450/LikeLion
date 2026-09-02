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


def local_questions(text: str, emotion: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).lower()
    ranked = []
    for pool in QUESTION_POOLS.values():
        score = sum(1 for keyword in pool["keywords"] if keyword in normalized)
        if score:
            ranked.append((score, pool["questions"]))
    ranked.sort(key=lambda item: item[0], reverse=True)
    candidates = []
    for _, questions in ranked[:2]:
        candidates.extend(questions)
    if emotion in ("지침", "불안", "슬픔", "외로움"):
        candidates.extend(QUESTION_POOLS["lonely"]["questions"])
    candidates.extend(GENERAL_QUESTIONS)
    unique = list(dict.fromkeys(candidates))
    seed = sum(ord(char) for char in normalized + emotion)
    random.Random(seed).shuffle(unique)
    return unique[:3]


def ai_questions(body: QuestionRequest) -> list[str] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    schema = {
        "type": "object",
        "properties": {"questions": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "string"}}},
        "required": ["questions"],
        "additionalProperties": False,
    }
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        "store": False,
        "instructions": (
            "당신은 가족 간 세대 공감 질문을 만드는 한국어 편집자다. 자녀의 구체적인 상황, 인물, 회사, 시험, 사건을 절대 드러내지 말고 "
            "부모 자신의 과거 경험을 자연스럽게 회고하게 하는 질문으로 위장한다. 잔소리나 해결책을 요구하지 말고, 서로 다른 관점의 질문 3개를 만든다. "
            "각 질문은 55자 안팎의 존댓말 한 문장이고, 원문의 표현을 그대로 복사하지 않는다. 자해·위기 표현이 있으면 위장하지 말고 도움 요청을 권하는 안전한 질문을 만든다."
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
        questions = json.loads(output_text or "{}").get("questions", [])
        return questions if len(questions) == 3 else None
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
        return None


def polish_local(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip().rstrip(". ")
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
    questions = ai_questions(body)
    source = "openai" if questions else "local"
    questions = questions or local_questions(body.worry, body.emotion)
    return {"question": questions[0], "questions": questions, "source": source, "mode": body.mode, "emotion": body.emotion, "privacy": "원문은 부모에게 전달되지 않습니다."}


@app.post("/api/answers/polish")
def polish(body: AnswerRequest):
    return {"polished": polish_local(body.answer), "original": body.answer}
