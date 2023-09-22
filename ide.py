import sys
import subprocess
import threading
import re

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import texts
import style

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

        self.text = QTextCharFormat()
        self.text.setForeground(QColor(255, 255, 255))

        self.main_syntax = QTextCharFormat()
        self.main_syntax.setForeground(QColor(255, 127, 0))

        self.digit = QTextCharFormat()
        self.digit.setForeground(QColor(0, 255, 255))

        self.string = QTextCharFormat()
        self.string.setForeground(QColor(0, 255, 0))

        self.function = QTextCharFormat()
        self.function.setForeground(QColor(191, 0, 255))

        self._mapping = {
            r'[^!]': self.text,
            
            r'(\w+)(?=\()': self.function,

            r'^(class|def|for|while|if|elif|else|try|except|finally|with|import)\b': self.main_syntax,
            r'^\s*from\s+|\s+s*import\b': self.main_syntax,
            r'\b(lambda|as|in|is|not|and|or|True|False|None|async|await)\b': self.main_syntax,

            r'\b\d+(\.\d+)?': self.digit,
            r'0b[0-1]+': self.digit,
            r'0o[0-7]+': self.digit,
            r'0x[0-9a-fA-F]+': self.digit,

            r'"([^"]*)"': self.string,
            r"'([^']*)'": self.string,
        }


class IdeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Vcode')
        self.resize(1000, 700)

        self.process = subprocess.Popen('python -V')
        self.process.wait()

        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.auto_save)
        self.setCentralWidget(self.editor)

        self.highlight = PythonHighlighter()
        self.highlight.setDocument(self.editor.document())

        self.file_menu = QMenu(self)
        self.menuBar().addMenu(self.file_menu)

        self.open_btn = QAction(self)
        self.open_btn.setShortcut(QKeySequence.StandardKey.Open)
        self.open_btn.triggered.connect(self.open_file)
        self.file_menu.addAction(self.open_btn)

        self.save_as_btn = QAction(self)
        self.save_as_btn.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_btn.triggered.connect(self.save_as)
        self.file_menu.addAction(self.save_as_btn)

        self.start_btn = QAction(self)
        self.start_btn.setShortcut(QKeySequence.StandardKey.Refresh)
        self.start_btn.triggered.connect(self.start_program)
        self.menuBar().addAction(self.start_btn)

        self.exit_btn = QAction(self)
        self.exit_btn.setShortcut(QKeySequence.StandardKey.Close)
        self.exit_btn.triggered.connect(self.close)
        self.menuBar().addAction(self.exit_btn)

        self.settings = QSettings('Vcode', 'Settings')
        if len(self.settings.allKeys()) == 3:
            self.editor.setFont(self.settings.value('Font'))
            self.select_language(self.settings.value('Language'))
            self.select_style(self.settings.value('Style'))
        else:
            self.settings.setValue('Font', QFont('JetBrains Mono', 12))
            self.select_language('en')
            self.select_style('Classic')

        self.filename = 'tests/m_t.py'
        self.saved_text = ''
        self.autosave = False

        with open(self.filename) as f:
            self.editor.setText(f.read())
        self.saved_text = self.editor.toPlainText()

    def select_language(self, language):
        self.settings.setValue('Language', language)

        self.file_menu.setTitle(texts.file_menu[language])
        self.open_btn.setText(texts.open_btn[language])
        self.save_as_btn.setText(texts.save_as_btn[language])
        self.start_btn.setText(texts.start_btn[language])
        self.exit_btn.setText(texts.exit_btn[language])

    def select_style(self, style_name):
        if style_name in style.STYLE.keys():
            self.settings.setValue('Style', style_name)
            self.setStyleSheet(style.STYLE[style_name])

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
        file, _ = QFileDialog.getOpenFileName(filter='Python Files (*.py *.pyw)')
        if file:
            self.filename = file
            with open(file) as of:
                self.editor.setText(of.read())
            self.saved_text = self.editor.toPlainText()

    def save_file(self):
        with open(self.filename, 'w') as sf:
            sf.write(self.editor.toPlainText())
        self.saved_text = self.editor.toPlainText()

    def save_as(self):
        path, _ = QFileDialog.getOpenFileName(filter='Python Files (*.py *.pyw)')
        if path:
            with open(path, 'w') as sf:
                sf.write(self.editor.toPlainText())

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


'''class SettingsDialog(QDialog):
    """QDialog with app settings"""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setModal(True)
        self.lay: QVBoxLayout = QVBoxLayout()

        self.style_select: QGroupBox = QGroupBox(self)
        style_select_layout: QVBoxLayout = QVBoxLayout()

        for st in 'style.keys()':
            st_rb: QRadioButton = QRadioButton(st, self)
            if st == self.parent().settings.value('style'):
                st_rb.setChecked(True)
            st_rb.clicked.connect(self.select_style_b)
            style_select_layout.addWidget(st_rb)

        self.style_select.setLayout(style_select_layout)

        self.autorun: QCheckBox = QCheckBox(self)
        self.lay.addWidget(self.autorun)

        self.show_autorun: QCheckBox = QCheckBox(self)
        self.lay.addWidget(self.show_autorun)

        self.top: QCheckBox = QCheckBox(self)
        self.lay.addWidget(self.top)

        self.doubleclick: QCheckBox = QCheckBox(self)
        self.lay.addWidget(self.doubleclick)

        self.language: QComboBox = QComboBox(self)
        self.language.addItems(['EN', 'RU', 'DE'])

        self.wgt: QWidget = QWidget()
        self.wgt.setLayout(self.lay)

        self.m_lay: QGridLayout = QGridLayout(self)
        self.m_lay.addWidget(self.style_select, 0, 0, 1, 1)
        self.m_lay.addWidget(self.wgt, 0, 1, 2, 1)
        self.m_lay.addWidget(self.language, 1, 0, 1, 1)
        self.setLayout(self.m_lay)'''


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IdeWindow()
    ide.show()
    sys.exit(app.exec())
