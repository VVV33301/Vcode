from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from .lineedit import LineEditMenu


class HighlightMakerString(QWidget):
    """Editor string for highlight maker"""

    def __init__(self, rstring: str, params: str) -> None:
        super().__init__()
        layout: QHBoxLayout = QHBoxLayout()
        self.setLayout(layout)

        self.rstring: QLineEdit = QLineEdit(rstring, self)
        self.rstring.contextMenuEvent = LineEditMenu(self.rstring)
        layout.addWidget(self.rstring)

        self.json_params: QLineEdit = QLineEdit(params[1:-1], self)
        self.json_params.contextMenuEvent = LineEditMenu(self.json_params)
        layout.addWidget(self.json_params)

        self.remove_btn: QPushButton = QPushButton('-', self)
        layout.addWidget(self.remove_btn)