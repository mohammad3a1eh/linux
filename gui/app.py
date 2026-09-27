"""Floating frameless voice assistant bubble with a system tray icon."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QStyle,
    QSystemTrayIcon,
)

from gui.signals import signals
from gui.widgets import VoiceAssistantAvatar

_DIAMETER = 180


class VoiceAssistantWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_offset = None

        self.setWindowTitle("Voice Assistant")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(_DIAMETER, _DIAMETER)

        self._menu = self._build_shared_menu()

        self.avatar = VoiceAssistantAvatar(diameter=_DIAMETER)
        self.setCentralWidget(self.avatar)
        signals.state_changed.connect(self.avatar.set_state)

    # ---------------------------------------------------------------- #
    #  Shared menu (used by both right-click and the tray icon)         #
    # ---------------------------------------------------------------- #
    def _build_shared_menu(self) -> QMenu:
        menu = QMenu(self)

        self._sleep_action = QAction("Toggle Sleep/Wake", self)
        self._sleep_action.setCheckable(True)
        self._sleep_action.triggered.connect(self._on_toggle_sleep)
        menu.addAction(self._sleep_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(quit_action)

        return menu

    def _on_toggle_sleep(self, checked: bool):
        signals.toggle_assistant.emit(not checked)

    def _on_quit(self):
        signals.text_updated.emit("quitting")
        QApplication.quit()

    def contextMenuEvent(self, event):
        self._menu.exec(event.globalPos())

    # ---------------------------------------------------------------- #
    #  Drag-to-move (no title bar)                                      #
    # ---------------------------------------------------------------- #
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if (
            self._drag_offset is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        event.accept()


class TrayIcon(QSystemTrayIcon):
    def __init__(self, menu: QMenu, parent=None):
        super().__init__(parent)
        icon = QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        )
        self.setIcon(icon)
        self.setToolTip("Voice Assistant")
        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            menu = self.contextMenu()
            if menu is not None:
                pos = QGuiApplication.cursor().pos()
                menu.popup(pos)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Assistant")
    app.setQuitOnLastWindowClosed(False)

    window = VoiceAssistantWindow()
    window.show()

    tray = TrayIcon(window._menu)
    tray.show()

    from core.engine import AssistantWorker

    worker = AssistantWorker()
    app.aboutToQuit.connect(worker.shutdown)
    worker.finished.connect(app.quit)
    worker.start()

    exit_code = app.exec()
    worker.shutdown()
    worker.wait(5000)
    tray.hide()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())