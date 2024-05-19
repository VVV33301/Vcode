from PyQt6.QtWidgets import QTabWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from classes.tabbar import TabBarMenu


class TabWidget(QTabWidget):
    """Custom QTabWidget"""

    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.lalay: QHBoxLayout = QHBoxLayout()
        self.empty_widget: QPushButton = QPushButton(self)
        self.lalay.addWidget(self.empty_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.lalay)
        self.currentChanged.connect(self.empty)

        self.mouseReleaseEvent = TabBarMenu(self, self.parent())

    def empty(self) -> None:
        """Show button when tab list is empty"""
        if not self.count():
            self.empty_widget.setVisible(True)
        else:
            self.empty_widget.setVisible(False)
