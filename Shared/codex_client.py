"""
Codex Cloud client — reads CODEX_API_KEY from env.
Returns None gracefully when key is absent (Phase A works without it).
"""
import os, json, logging
import requests

logger = logging.getLogger(__name__)

CODEX_ENDPOINT = os.getenv(
    "CODEX_API_ENDPOINT",
    "https://api.openai.com/v1/chat/completions"  # default OpenAI endpoint
)

def load_api_key() -> str | None:
    return os.getenv("CODEX_API_KEY")

def generate_code(prompt: str, model: str = "gpt-4o", temperature: float = 0.2) -> str | None:
    api_key = load_api_key()
    if not api_key:
        logger.info("CODEX_API_KEY not set — skipping Codex call.")
        return None

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 2048,
    }
    try:
        resp = requests.post(CODEX_ENDPOINT, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Codex call failed: {e}")
        return None
