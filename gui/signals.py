"""Thread-safe notification bridge between the AI pipeline and the Qt UI.

Example — background thread emits (Qt auto-queues cross-thread signal delivery):
    from gui.signals import signals

    signals.state_changed.emit("listening")

Example — GUI connects:
    from gui.signals import signals

    signals.state_changed.connect(lambda state: print(f"State: {state}"))
"""

from PySide6.QtCore import QObject, Signal


class AssistantSignals(QObject):
    state_changed = Signal(str)
    text_updated = Signal(str)
    toggle_assistant = Signal(bool)


signals = AssistantSignals()