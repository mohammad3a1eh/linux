# linux

```text
my_assistant/
├── main.py                 # Main application entry point (Initializes GUI and spawns processing threads)
├── config.py               # Global configurations (Model paths, mic sensitivity, system prompts)
├── requirements.txt        # Python dependencies list
│
├── core/                   # Core AI and processing engine
│   ├── __init__.py
│   ├── wakeword.py         # Microphone management and openWakeWord integration
│   ├── stt.py              # Speech-to-Text processing (Vosk / Whisper)
│   ├── tts.py              # Text-to-Speech generation (Piper)
│   └── llm.py              # Ollama integration and prompt injection management
│
├── routing/                # Intent routing and decision making
│   ├── __init__.py
│   ├── semantic_router.py  # Semantic Router configuration for intent detection
│   └── prompt_builder.py   # Merges local data with user queries to build LLM prompts
│
├── modules/                # Local capabilities and task execution
│   ├── __init__.py
│   ├── system_info.py      # Extracts CPU, RAM, and temperature metrics (via psutil)
│   ├── media_control.py    # System volume and media playback control
│   └── weather.py          # Placeholder for future weather API integration
│
├── gui/                    # GTK4 + Libadwaita native graphical interface
│   ├── __init__.py
│   ├── app.py              # Main window structure and GTK application loop
│   ├── widgets.py          # Custom UI components (Microphone buttons, status animations)
│   └── signals.py          # Thread communication management between AI engine and GUI
│
├── models/                 # Offline model files directory (Ignored in version control)
│   ├── wakeword/           # .onnx wake word models
│   ├── stt/                # Vosk or Whisper model directories
│   └── tts/                # Piper voice models
│
└── assets/                 # Static application assets
    ├── icons/              # Application and UI icons (SVG)
    └── sounds/             # Sound effects (e.g., wake word activation chime)
```