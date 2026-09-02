"""질문/답변 서비스가 함께 쓰는 OpenAI 통신부."""

import json
import os
import urllib.error
import urllib.request


def request_structured_output(
    *,
    instructions: str,
    input_text: str,
    schema_name: str,
    schema: dict,
    max_output_tokens: int = 500,
) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        "store": False,
        "instructions": instructions,
        "input": input_text,
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": schema,
            }
        },
        "max_output_tokens": max_output_tokens,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
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

        return json.loads(output_text or "{}")
    except (
        urllib.error.URLError,
        TimeoutError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ):
        return None
