from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from PyQt6.QtGui import QTextCursor
from .editortab import EditorTab
from .lineedit import LineEditMenu
import texts


class FindWindow(QDialog):
    """Find all text usages of string"""

    def __init__(self, parent: EditorTab | None = None) -> None:
        super().__init__(parent)
        self.parent: EditorTab = parent
        self.setModal(True)
        self.setMinimumSize(400, 150)
        layout: QVBoxLayout = QVBoxLayout(self)
        self.setLayout(layout)
        self.setWindowTitle(texts.find_btn[self.parent.pr_settings.value('Language')])

        self.find_line: QLineEdit = QLineEdit(self)
        self.find_line.textChanged.connect(self.search)
        self.find_line.contextMenuEvent = LineEditMenu(self.find_line)
        layout.addWidget(self.find_line)

        self.list: QListWidget = QListWidget(self)
        self.list.itemClicked.connect(self.go_to_line)
        layout.addWidget(self.list)

        self.counter: QLabel = QLabel('Total results: 0', self)
        layout.addWidget(self.counter)

    def search(self) -> None:
        """Scat text for search usages"""
        self.list.clear()
        find: str = self.find_line.text()
        if find:
            text: list[str] = self.parent.toPlainText().split('\n')
            for i in range(self.parent.blockCount()):
                if find in text[i].lower():
                    self.list.addItem(f'Line {i}: "{text[i]}"')
        self.counter.setText(f'Total results: {self.list.count()}')

    def go_to_line(self, key: QListWidgetItem) -> None:
        """Open selected line in text"""
        self.parent.setTextCursor(
            QTextCursor(self.parent.document().findBlockByLineNumber(int(key.text()[5:].split(':')[0]))))
