from PyQt6.QtWidgets import QWidget, QListWidget, QDialog, QVBoxLayout, QPushButton, QFileDialog
from os.path import isfile
from shutil import copy2
from functions import resource_path
from default import CONFIG_PATH


class ExtensionsSettings(QDialog):
    """Extension settings dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent: QWidget = parent
        layout: QVBoxLayout = QVBoxLayout()
        self.setLayout(layout)

        self.list: QListWidget = QListWidget(self)
        layout.addWidget(self.list)

        self.import_btn: QPushButton = QPushButton(self)
        self.import_btn.clicked.connect(self.import_ext)
        layout.addWidget(self.import_btn)

    def import_ext(self):
        proj: str = QFileDialog.getOpenFileName(directory='/', filter='Extensions Files (*.py)')[0].replace('\\', '/')
        if proj and isfile(proj) and proj.endswith('.py'):
            copy2(proj, resource_path(CONFIG_PATH + '/extensions'))
            self.parent.restart()
