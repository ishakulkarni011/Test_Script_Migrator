import os
import logging
import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from llm_client import generate_code_with_ollama, LLMError
from post_process import strip_code_fences, ensure_python_file_header
load_dotenv()
logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="Test Script Migration")

ALLOWED_FRAMEWORKS = {"pytest", "unittest", "bdd"}
class ConvertRequest(BaseModel):
    filename: str
    framework: str
    source: str

class ConvertResponse(BaseModel):
    python_code: str

@app.get("/health")
def health():
    return {
        "status": "ok",
        "provider": os.getenv("LLM_PROVIDER", "ollama"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", ""),
        "model": os.getenv("OLLAMA_MODEL", ""),
        "timeout_seconds": os.getenv("LLM_TIMEOUT_SECONDS", "180"),
        "allowed_frameworks": sorted(list(ALLOWED_FRAMEWORKS)),
    }

@app.post("/convert", response_model=ConvertResponse)
async def convert(req: ConvertRequest):
    framework = req.framework.lower().strip()

    # Normalize legacy / friendly labels into canonical framework keys
    if framework in {"behave", "bdd (behave)", "bdd"}:
        framework = "bdd"

    if framework not in ALLOWED_FRAMEWORKS:
        raise HTTPException(status_code=400, detail=f"Unsupported framework: {framework}")

    max_chars = int(os.getenv("MAX_INPUT_CHARS", "120000"))
    if len(req.source) > max_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Input too large ({len(req.source)} chars). Max allowed is {max_chars}."
        )

    user_prompt = USER_PROMPT_TEMPLATE.format(
        framework=framework,
        filename=req.filename,
        source=req.source
    )

    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider != "ollama":
        raise HTTPException(status_code=500, detail="This project is configured for free local Ollama only.")

    try:
        raw = await generate_code_with_ollama(SYSTEM_PROMPT, user_prompt)
        cleaned = ensure_python_file_header(strip_code_fences(raw))
        return ConvertResponse(python_code=cleaned)

    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))

    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Unhandled exception in /convert:\n%s", tb)
        msg = str(e) if str(e) else e.__class__.__name__
        raise HTTPException(status_code=500, detail=f"Unexpected error: {msg}")
