import json
import os
import urllib.error
import urllib.request

def _call_gemini(*, api_key: str, instructions: str, input_text: str, schema: dict, max_output_tokens: int = 500) -> dict | None:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        prompt = f"{instructions}\n\n[반환 형식]\n반드시 순수 JSON으로만 응답하세요.\n스키마: {json.dumps(schema, ensure_ascii=False)}"
        model = genai.GenerativeModel(model_name=model_name, generation_config={"response_mime_type": "application/json", "max_output_tokens": max_output_tokens, "temperature": 0.7})
        response = model.generate_content([prompt, input_text])
        if response and response.text:
            return json.loads(response.text.strip())
    except Exception as e:
        print(f"[Gemini Error] {e}")
    return None

def _call_openai(*, api_key: str, instructions: str, input_text: str, schema_name: str, schema: dict, max_output_tokens: int = 500) -> dict | None:
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "store": False,
        "instructions": instructions,
        "input": input_text,
        "text": {"format": {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}},
        "max_output_tokens": max_output_tokens,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
        output_text = result.get("output_text")
        if not output_text:
            for item in result.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        output_text = content.get("text")
                        break
        return json.loads(output_text or "{}")
    except Exception as e:
        print(f"[OpenAI Error] {e}")
    return None

def request_structured_output(*, instructions: str, input_text: str, schema_name: str, schema: dict, max_output_tokens: int = 500) -> dict | None:
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if gemini_key:
        res = _call_gemini(api_key=gemini_key, instructions=instructions, input_text=input_text, schema=schema, max_output_tokens=max_output_tokens)
        if res:
            return {**res, "_provider": "gemini"}
    if openai_key:
        res = _call_openai(api_key=openai_key, instructions=instructions, input_text=input_text, schema_name=schema_name, schema=schema, max_output_tokens=max_output_tokens)
        if res:
            return {**res, "_provider": "openai"}
    return None
