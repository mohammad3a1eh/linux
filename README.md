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

## Installation & Setup

### 1. System dependencies (Debian)

```bash
sudo apt install \
    python3-venv \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    gir1.2-adw-1 \
    libcairo2-dev \
    libgirepository1.0-dev \
    portaudio19-dev \
    libportaudio2
```

- `python3-venv` — virtual environments.
- `python3-gi`, `python3-gi-cairo` — PyGObject (GObject Introspection 3.x and its Cairo bindings).
- `gir1.2-gtk-4.0`, `gir1.2-adw-1` — GTK4 and Libadwaita GObject introspection files (required for `gi` to load the toolkits).
- `libcairo2-dev`, `libgirepository1.0-dev` — headers needed to build/compile PyGObject and C extensions.
- `portaudio19-dev` — headers needed to build `sounddevice` from source.
- `libportaudio2` — runtime PortAudio library required by `sounddevice` at import time.

### 2. Python virtual environment

On Debian, PyGObject is a system package (`python3-gi`) and **won't build against a clean venv without extra toolchain+meson setup**. Because of this it's strongly recommended to create the venv **with `--system-site-packages`**. That keeps the system's compiled PyGObject/Cairo bindings visible inside the venv while still isolating your pip-installed packages:

```bash
# --system-site-packages is strongly recommended on Debian
python3 -m venv --system-site-packages venv
```

Alternative (not recommended): a clean venv builds PyGObject from source and requires Ninja/Meson plus more dev headers.

### 3. Activate and install requirements

```bash
# Activate
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# openwakeword declares tflite-runtime, which has no wheels for
# Python >= 3.13 — so install it without deps (its runtime deps
# are already in requirements.txt):
pip install --no-deps openwakeword==0.6.0
```

### 4. Verify

```bash
python -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw; print('GTK4+Adw OK')"
```