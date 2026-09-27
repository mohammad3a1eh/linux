"""Semantic routing with HuggingFace encoder + ToolBox."""

import os
import platform
import sys
from datetime import datetime
from pathlib import Path

for _p in (Path(__file__).resolve().parents[1],):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import config

# MUST run before any transformer/encoder import — pins HF download location.
_CACHE = os.path.abspath(config.EMBEDDING_CACHE_DIR)
os.environ["HF_HOME"] = _CACHE
os.environ["SENTENCE_TRANSFORMERS_HOME"] = _CACHE


class ToolBox:
    @staticmethod
    def get_time_date() -> str:
        now = datetime.now()
        return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({platform.node()})"

    @staticmethod
    def get_system_resources() -> str:
        import psutil

        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        return f"CPU usage: {cpu}%  RAM usage: {ram}%"

    @staticmethod
    def get_os_info() -> str:
        return f"OS: {platform.system()} {platform.release()} ({platform.version()})"


_ROUTES = [
    dict(
        name="time_date",
        utterances=[
            "what time is it",
            "what is the current date",
            "tell me the date and time",
            "what is today's date",
            "what day is it now",
        ],
    ),
    dict(
        name="system_resources",
        utterances=[
            "what is my cpu usage",
            "how much ram is being used",
            "show me system resources",
            "cpu and memory usage",
            "what is the current ram usage",
        ],
    ),
    dict(
        name="os_info",
        utterances=[
            "what operating system am I using",
            "show os version",
            "what is my os name",
            "which linux distro is this",
            "tell me the os info",
            "what is your name?"
        ],
    ),
]

_NAME_TO_TOOL = {
    "time_date": ToolBox.get_time_date,
    "system_resources": ToolBox.get_system_resources,
    "os_info": ToolBox.get_os_info,
}


class IntentRouter:
    def __init__(self):
        # This file shadows the installed `semantic_router` package when
        # routing/ is on sys.path — prune our own dir first.
        _self_dir = str(Path(__file__).resolve().parent)
        sys.path = [p for p in sys.path if p and Path(p).resolve() != Path(_self_dir).resolve()]
        if "semantic_router" in sys.modules:
            del sys.modules["semantic_router"]
        from semantic_router import Route, SemanticRouter
        from semantic_router.encoders import HuggingFaceEncoder

        encoder = HuggingFaceEncoder(name="sentence-transformers/all-MiniLM-L6-v2")
        self._Route = Route
        self._router = SemanticRouter(
            encoder=encoder,
            routes=[Route(**rd) for rd in _ROUTES],
            auto_sync="local",
        )

    def process_query(self, user_text: str):
        choice = self._router(user_text)
        if choice is None or choice.name is None:
            return None, None
        tool = _NAME_TO_TOOL.get(choice.name)
        if tool is None:
            return choice.name, None
        try:
            data = tool()
        except Exception as exc:
            data = f"[tool error: {exc}]"
        return choice.name, data


if __name__ == "__main__":
    print(f"Embedding cache: {_CACHE}")
    router = IntentRouter()
    tests = [
        "what time is it right now",
        "show me cpu and ram usage",
        "what operating system is this",
        "hello how are you today",
    ]
    for q in tests:
        name, data = router.process_query(q)
        if name:
            print(f"→ {q!r}  matched={name!r}  data={data!r}")
        else:
            print(f"→ {q!r}  no match")
