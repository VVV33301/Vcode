from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from .lineedit import LineEditMenu


class InputDialog(QDialog):
    """Custom QInputDialog"""

    def __init__(self, title: str, text: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle(title)
        self.l: QVBoxLayout = QVBoxLayout(self)
        self.l.addWidget(QLabel(text, self))
        self.le: QLineEdit = QLineEdit(self)
        self.le.contextMenuEvent = LineEditMenu(self.le)
        self.l.addWidget(self.le)
        self.ok_btn: QPushButton = QPushButton('OK', self)
        self.ok_btn.clicked.connect(self.accept)
        self.l.addWidget(self.ok_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def text_value(self) -> str:
        """Returns entered text"""
        return self.le.text()
