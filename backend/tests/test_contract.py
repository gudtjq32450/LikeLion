import os
import sys
import unittest


BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from schemas.answer import AnswerRequest
from schemas.question import QuestionRequest
from services.answer_service import polish_answer
from services.question_service import transform_question


class ApiContractTest(unittest.TestCase):
    def setUp(self):
        self.previous_key = os.environ.pop("OPENAI_API_KEY", None)

    def tearDown(self):
        if self.previous_key is not None:
            os.environ["OPENAI_API_KEY"] = self.previous_key

    def test_existing_routes_are_preserved(self):
        paths = set(app.openapi()["paths"])
        self.assertIn("/", paths)
        self.assertIn("/api/health", paths)
        self.assertIn("/api/questions/transform", paths)
        self.assertIn("/api/answers/polish", paths)

    def test_question_local_fallback_contract(self):
        result = transform_question(
            QuestionRequest(worry="면접에서 계속 떨어져서 힘들어", emotion="지침", mode="stealth")
        )
        self.assertEqual(result["source"], "local")
        self.assertEqual(result["mode"], "stealth")
        self.assertEqual(result["emotion"], "지침")
        self.assertEqual(len(result["questions"]), 5)
        self.assertIn(result["target_question"], result["questions"])
        self.assertEqual(result["question"], result["questions"][0])

    def test_answer_local_fallback_contract(self):
        original = "나도 처음엔 막막했지만 그냥 버텼어"
        result = polish_answer(
            AnswerRequest(answer=original, question="실패했을 때 어떻게 견뎠나요?")
        )
        self.assertEqual(result["source"], "local")
        self.assertEqual(result["original"], original)
        self.assertTrue(result["polished"])


if __name__ == "__main__":
    unittest.main()
