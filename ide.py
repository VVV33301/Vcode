from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys

import subprocess
import threading

import re

from traceback import print_exc


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument = None):
        super().__init__(parent)
        self._mapping = {}

    def highlightBlock(self, text: str) -> None:
        for pattern, style in self._mapping.items():
            for match in re.finditer(pattern, text):
                s, e = match.span()
                self.setFormat(s, e-s, style)


class PythonHighlighter(Highlighter):
    def __init__(self, parent: QTextDocument = None):
        super().__init__(parent)

        self.main_syntax = QTextCharFormat()
        self.main_syntax.setForeground(QColor(255, 0, 0))

        self.digit = QTextCharFormat()
        self.digit.setForeground(QColor(0, 255, 255))

        self.string = QTextCharFormat()
        self.string.setForeground(QColor(0, 255, 0))

        self.function = QTextCharFormat()
        self.function.setForeground(QColor(0, 0, 255))

        self._mapping = {
            r'^\s*class\s+': self.main_syntax,
            r'^\s*def\s+': self.main_syntax,
            r'^\s*for\s+': self.main_syntax,
            r'^\s*while\s+': self.main_syntax,
            r'^\s*if\s+': self.main_syntax,
            r'^\s*elif\s+': self.main_syntax,
            r'^\s*else': self.main_syntax,
            r'^\s*try': self.main_syntax,
            r'^\s*except': self.main_syntax,
            r'^\s*finally': self.main_syntax,
            r'^\s*with': self.main_syntax,
            r'^\s*import\s+': self.main_syntax,
            r'^\s*from\s+|\s+s*import\s+': self.main_syntax,
            r'\s*lambda': self.main_syntax,
            r'\s+\s*as\s+|\s+\s*in\s+|\s+\s*is\s+': self.main_syntax,

            r'"([^"]*)"': self.string,
            r"'([^']*)'": self.string,

            r'(?<![\'"])\b\d+\.\d+|\b\d+\b(?!["\'])': self.digit,
            r'0b[0-1]+': self.digit,
            r'0o[0-7]+': self.digit,
            r'0x[0-9a-fA-F]+': self.digit,

            r'(\w+)(?=\()': self.function,
        }


class IdeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('IDE')
        self.resize(500, 500)

        self.process = subprocess.Popen('python -V')
        self.process.wait()

        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.auto_save)
        self.setCentralWidget(self.editor)

        self.highlight = PythonHighlighter()
        self.highlight.setDocument(self.editor.document())

        self.file_m = QMenu('File', self)
        self.menuBar().addMenu(self.file_m)

        self.open_btn = QAction('Open', self)
        self.open_btn.setShortcut(QKeySequence.StandardKey.Open)
        self.open_btn.triggered.connect(self.open_file)
        self.file_m.addAction(self.open_btn)

        self.start_btn = QAction('Start', self)
        self.start_btn.setShortcut(QKeySequence.StandardKey.Refresh)
        self.start_btn.triggered.connect(self.start_program)
        self.menuBar().addAction(self.start_btn)

        self.exit_btn = QAction('Exit', self)
        self.exit_btn.setShortcut(QKeySequence.StandardKey.Close)
        self.exit_btn.triggered.connect(self.close)
        self.menuBar().addAction(self.exit_btn)

        self.settings = QSettings('Vcode', 'Settings')
        if self.settings.value('Font'):
            self.editor.setFont(self.settings.value('Font'))
        else:
            self.settings.setValue('Font', QFont('Arial', 12))

        self.filename = 'tests/m_t.py'
        self.saved_text = ''
        self.autosave = False

        with open(self.filename) as f:
            self.editor.setText(f.read())
        self.saved_text = self.editor.toPlainText()

    def start_program(self):
        if not self.autosave and self.saved_text != self.editor.toPlainText():
            a = QMessageBox.warning(self, 'Warning', 'Do you want to save changes?',
                                    buttons=QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
                                    defaultButton=QMessageBox.StandardButton.Save)
            if a == QMessageBox.StandardButton.Cancel:
                return
            else:
                self.save_file()
        self.process.terminate()
        threading.Thread(target=self.program).start()

    def program(self):
        self.process = subprocess.Popen(f'python {self.filename}')
        print(f'\033[1m\033[93mExit code: {self.process.wait()}\033[0m\n')

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(caption='Open new file...', filter='Python Files (*.py *.pyw)')
        if file:
            self.filename = file
            with open(file) as of:
                self.editor.setText(of.read())
            self.saved_text = self.editor.toPlainText()

    def save_file(self):
        with open(self.filename, 'w') as sf:
            sf.write(self.editor.toPlainText())
        self.saved_text = self.editor.toPlainText()

    def auto_save(self):
        if self.autosave:
            self.saved_text = self.editor.toPlainText()
            self.save_file()

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.process.returncode is None:
            a = QMessageBox.warning(self, 'Warning', 'Do you want to terminate process?',
                                    buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                                    defaultButton=QMessageBox.StandardButton.Ok)
            if a == QMessageBox.StandardButton.Cancel:
                a0.ignore()
            else:
                self.process.terminate()
        if self.saved_text != self.editor.toPlainText():
            a = QMessageBox.warning(self, 'Warning', 'Do you want to save changes?',
                                    buttons=QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard |
                                            QMessageBox.StandardButton.Cancel,
                                    defaultButton=QMessageBox.StandardButton.Save)
            if a == QMessageBox.StandardButton.Cancel:
                a0.ignore()
            elif a == QMessageBox.StandardButton.Save:
                self.save_file()
                a0.accept()
            else:
                a0.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IdeWindow()
    ide.show()
    sys.exit(app.exec())
