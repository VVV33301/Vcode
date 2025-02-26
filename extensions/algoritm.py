from PyQt6.QtWidgets import QPushButton, QLineEdit, QWidget, QTextEdit, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, QObject


class Algoritm(QWidget):
    TEXTS = {'out': {'en': 'Sorry, this extension now in development',
                     'ru': 'Извините, расширение находится в разработке'}}

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def select_language(self, language):
        if language in ('en', 'ru'):
            self.output.setText(self.TEXTS['out'][language])
        else:
            self.output.setText(self.TEXTS['out']['en'])


def main(ide):
    algoritm = Algoritm(ide)
    ide.extensions.addTab(algoritm, 'Algoritm')
