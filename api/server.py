"""OpenAI-compatible REST API for the voice assistant LLM + tools.

Run alongside or independently of the voice daemon:
    uvicorn api.server:app --host 127.0.0.1 --port 8000
"""

import asyncio
import logging
import time
import uuid
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import config
from config import LLM_MODEL_NAME
from core.llm import LocalLLM

_LOG = logging.getLogger(__name__)

app = FastAPI(title="Voice Assistant API", version="1.0.0")

llm: LocalLLM | None = None
_llm_lock = asyncio.Lock()


class ChatMessage(BaseModel):
    role: str = Field(description="system | user | assistant | tool")
    content: str = Field(description="Message text")


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(description="Conversation history")
    model: Optional[str] = Field(default=None, description="Optional model override")
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = Field(default=False, description="Streaming not supported")


def _load_llm(model: str | None = None) -> LocalLLM:
    global llm
    name = model or config.LLM_MODEL_NAME
    if llm is None or (model and llm.model_name != model):
        _LOG.info("Initializing LocalLLM (model=%s)", name)
        llm = LocalLLM(model_name=name)
    return llm


def _get_context() -> str | None:
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        return f"CPU: {cpu}%  RAM: {mem}%"
    except Exception:
        return None


def _latest_user_text(messages: list[ChatMessage]) -> str:
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    raise HTTPException(status_code=400, detail="No user message in payload")


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest) -> dict[str, Any]:
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")
    if req.stream:
        raise HTTPException(status_code=400, detail="streaming not supported")

    user_text = _latest_user_text(req.messages)
    instance = _load_llm(req.model)
    context = _get_context()

    async with _llm_lock:
        try:
            reply = await asyncio.to_thread(
                instance.generate_response, user_text, system_data=context
            )
        except Exception as exc:
            _LOG.exception("LLM error")
            raise HTTPException(status_code=500, detail=str(exc))

    created = int(time.time())
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    model_name = req.model or instance.model_name
    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": created,
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": -1,
            "completion_tokens": -1,
            "total_tokens": -1,
        },
    }


@app.get("/v1/models")
async def list_models() -> dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": LLM_MODEL_NAME,
                "object": "model",
                "created": 1686935002,
                "owned_by": "local-assistant",
            }
        ],
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="127.0.0.1", port=8000)
