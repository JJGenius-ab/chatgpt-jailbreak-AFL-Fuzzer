import asyncio
import os
from functools import lru_cache

try:
    import google.generativeai as genai
except ImportError:
    genai = None


MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


@lru_cache(maxsize=1)
def _get_model():
    if genai is None:
        raise RuntimeError(
            "google-generativeai is not installed. Install it with "
            "`pip install google-generativeai`."
        )

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable is not set.")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_NAME)


async def query_llm(prompt: str) -> str:
    try:
        model = _get_model()
        response = await asyncio.to_thread(model.generate_content, prompt)
        return getattr(response, "text", "") or ""
    except Exception as e:
        print(f"[Gemini ERROR] {e}")
        return ""
