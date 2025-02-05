from PyQt6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QToolBar, QWidgetAction, QWidget, QPlainTextEdit, \
    QVBoxLayout
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import QUrl, pyqtSlot, QCoreApplication, Qt

import requests

class AaronAIWindow(QWidget):
    TEXTS = {'input': {'en': 'Input text here', 'ru': 'Введите текст здесь'},
             'generate': {'en': 'Generate', 'ru': 'Сгенерировать'}}

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.input = QLineEdit(self)
        layout.addWidget(self.input)

        self.output = QPlainTextEdit(self)
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.generate_btn = QPushButton(self)
        layout.addWidget(self.generate_btn)

    def generate(self):
        pass

    def select_language(self, language):
        if language in ('en', 'ru'):
            self.input.setPlaceholderText(self.TEXTS['input'][language])
            self.generate_btn.setText(self.TEXTS['generate'][language])
        else:
            self.input.setPlaceholderText(self.TEXTS['input']['en'])
            self.generate_btn.setText(self.TEXTS['generate']['en'])


def main(ide):
    ide.aaron = AaronAIWindow(ide)
    ide.splitter.addWidget(ide.aaron)