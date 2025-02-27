import threading
from PyQt6.QtWidgets import QPushButton, QLineEdit, QWidget, QTextEdit, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, QObject
import requests


class AaronAIWindow(QWidget):
    TEXTS = {'input': {'en': 'Input text here', 'ru': 'Введите текст здесь'},
             'generate': {'en': 'Generate', 'ru': 'Сгенерировать'},
             'waiting': {'en': 'Waiting...', 'ru': 'Генерация...'},
             'fail': {'en': 'Failed to get response. Please try again',
                      'ru': 'Произошла ошибка при получении ответа. Попробуйте ещё раз'}}

    class Request(QObject):
        out_recieved = pyqtSignal(str)
        URL = 'http://bilet.tatar:8080/api/chat/completions'
        HEADERS = {'Authorization': 'Bearer sk-ccbfecb8062748dc8e42a29c07dd745a',
                   'Content-Type': 'application/json'}

        def __init__(self, text, fail_text):
            super().__init__()
            self.text = text
            self.fail_text = fail_text

        def run(self):
            try:
                req = requests.post(self.URL, headers=self.HEADERS, json={'model': 'qwen2.5-coder:3b', 'messages':
                    [{'role': 'user', 'content': self.text}]})
            except requests.exceptions.ConnectTimeout:
                self.out_recieved.emit(self.fail_text)
                return
            if req.status_code == 200:
                self.out_recieved.emit(req.json()['choices'][0]['message']['content'])
            else:
                req = requests.post(self.URL, headers=self.HEADERS, json={'model': 'mistral:7b', 'messages':
                    [{'role': 'user', 'content': self.text}]})
                if req.status_code == 200:
                    self.out_recieved.emit(req.json()['choices'][0]['message']['content'])
                else:
                    self.out_recieved.emit(self.fail_text)

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
        self.resp_fail_text = ''

    def generate(self):
        if not self.input.text():
            return
        self.output.setMarkdown(self.output.toMarkdown() + '\n## ' + self.input.text() +
            '\n### ' + self.TEXTS['waiting'][self.curr_lang])
        self.generate_btn.setEnabled(False)
        request = self.Request(self.input.text(), self.resp_fail_text)
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
            self.resp_fail_text = self.TEXTS['fail'][language]
            self.curr_lang = language
        else:
            self.input.setPlaceholderText(self.TEXTS['input']['en'])
            self.generate_btn.setText(self.TEXTS['generate']['en'])
            self.resp_fail_text = self.TEXTS['fail']['en']
            self.curr_lang = 'en'


def main(ide):
    aaron = AaronAIWindow(ide)
    ide.extensions.addTab(aaron, 'Aaron AI')
