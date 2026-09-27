"""Project-wide configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent

WAKEWORD_MODEL_PATH = os.getenv(
    "WAKEWORD_MODEL_PATH",
    "models/wakeword/Hey_Linux_20260901_220044.onnx",
)

STT_MODEL_PATH = os.getenv(
    "STT_MODEL_PATH",
    "models/stt/vosk-model-small-fa-0.5",
)

LLM_MODEL_NAME = os.getenv(
    "LLM_MODEL_NAME",
    "gemma4:e2b",
)

TTS_MODEL_PATH = os.getenv(
    "TTS_MODEL_PATH",
    "models/tts/fa_IR-mana-medium.onnx",
)

TTS_CONFIG_PATH = os.getenv(
    "TTS_CONFIG_PATH",
    "models/tts/fa_IR-mana-medium.onnx.json",
)

ACTIVATION_SHORTCUT = os.getenv(
    "ACTIVATION_SHORTCUT",
    "<F7>",
)

EMBEDDING_CACHE_DIR = os.getenv(
    "EMBEDDING_CACHE_DIR",
    "models/embeddings",
)
