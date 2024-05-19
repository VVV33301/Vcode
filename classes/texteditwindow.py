from PyQt6.QtWidgets import QTextEdit, QPlainTextEdit
from PyQt6.QtGui import QAction, QContextMenuEvent
from .textedit import TextEditMenu
import texts


class TextEditWindowMenu(TextEditMenu):
    """TextEditMenu for windows"""

    def __init__(self, parent: QTextEdit | QPlainTextEdit, ide, *args, **kwargs) -> None:
        super().__init__(parent=parent, ide=ide, *args, **kwargs)

        self.addSeparator()

        self.exit: QAction = QAction(self)
        self.exit.triggered.connect(lambda: ide.close_window_mode(parent))
        self.exit.setShortcut('Alt+F4')
        self.addAction(self.exit)

    def __call__(self, event: QContextMenuEvent) -> None:
        lang: str = self.lang_s.value('Language')
        self.exit.setText(texts.close_btn[lang])
        super().__call__(event)
