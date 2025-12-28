import os
import httpx

class LLMError(RuntimeError):
    pass

async def generate_code_with_ollama(system_prompt: str, user_prompt: str) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.1")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    timeout_s = float(os.getenv("LLM_TIMEOUT_SECONDS", "180"))

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    }

    timeout = httpx.Timeout(timeout_s, connect=30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(f"{base_url}/api/chat", json=payload)
        except httpx.ConnectError as e:
            raise LLMError(f"Cannot connect to Ollama at {base_url}. Is `ollama serve` running? ({e})")
        except httpx.ReadTimeout as e:
            raise LLMError(f"Ollama timed out after {timeout_s}s (ReadTimeout). Increase LLM_TIMEOUT_SECONDS. ({e})")

        if r.status_code != 200:
            raise LLMError(f"Ollama error {r.status_code}: {r.text}")

        data = r.json()
        return data["message"]["content"]