from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPaintEvent


class LineNumberArea(QWidget):
    """Area for numbers of lines"""

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self.editor = editor

    def paintEvent(self, event: QPaintEvent) -> None:
        self.editor.update_line_event(event)
