import threading
from PyQt6.QtWidgets import QPushButton, QLineEdit, QWidget, QTextEdit, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, QObject
import requests


class AaronAIWindow(QWidget):
    TEXTS = {'input': {'en': 'Input text here', 'ru': 'Введите текст здесь'},
             'generate': {'en': 'Generate', 'ru': 'Сгенерировать'},
             'waiting': {'en': 'Waiting...', 'ru': 'Генерация...'}}

    class Request(QObject):
        out_recieved = pyqtSignal(str)

        def __init__(self, text):
            super().__init__()
            self.text = text

        def run(self):
            req = requests.post('http://bilet.tatar:8080/api/chat/completions',
                                headers={'Authorization': 'Bearer sk-ccbfecb8062748dc8e42a29c07dd745a',
                                         'Content-Type': 'application/json'},
                                json={'model': 'mistral:7b', 'messages':
                                    [{'role': 'user', 'content': self.text}]})
            if req.status_code == 200:
                self.out_recieved.emit(req.json()['choices'][0]['message']['content'])

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.input = QLineEdit(self)
        self.input.setClearButtonEnabled(True)
        self.input.returnPressed.connect(self.generate)
        layout.addWidget(self.input)

        self.generate_btn = QPushButton(self)
        self.generate_btn.clicked.connect(self.generate)
        layout.addWidget(self.generate_btn)

        self.curr_lang = 'en'

    def generate(self):
        if not self.input.text():
            return
        self.output.setMarkdown(self.output.toMarkdown() + '\n## ' + self.input.text() +
            '\n### ' + self.TEXTS['waiting'][self.curr_lang])
        self.generate_btn.setEnabled(False)
        request = self.Request(self.input.text())
        request.out_recieved.connect(self.print_output)
        threading.Thread(target=request.run, daemon=True).start()

    def print_output(self, text):
        t = self.output.toMarkdown()
        self.output.setMarkdown(t[:t.rfind('###')] + text)
        self.input.clear()
        self.generate_btn.setEnabled(True)

    def select_language(self, language):
        if language in ('en', 'ru'):
            self.input.setPlaceholderText(self.TEXTS['input'][language])
            self.generate_btn.setText(self.TEXTS['generate'][language])
            self.curr_lang = language
        else:
            self.input.setPlaceholderText(self.TEXTS['input']['en'])
            self.generate_btn.setText(self.TEXTS['generate']['en'])
            self.curr_lang = 'en'


def main(ide):
    aaron = AaronAIWindow(ide)
    ide.extensions.addTab(aaron, 'Aaron AI')
