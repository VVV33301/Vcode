import sys
import subprocess
import threading
import re
import json
from winreg import HKEYType, HKEY_CURRENT_USER, KEY_ALL_ACCESS, REG_SZ, OpenKey, SetValueEx, DeleteValue

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import texts
from style import STYLE
from highlights.languages_list import languages, start_command

from traceback import print_exc


def set_autorun(enabled: bool) -> None:
    key: HKEYType = OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                            0, KEY_ALL_ACCESS)
    if enabled:
        SetValueEx(key, 'Vcode', 0, REG_SZ, sys.argv[0])
    else:
        DeleteValue(key, 'Vcode')
    key.Close()


class Highlighter(QSyntaxHighlighter):
    def __init__(self, highlight_path: str, parent: QTextDocument = None):
        super().__init__(parent)
        self._mapping = {}
        with open(highlight_path) as highlight_file:
            for string in highlight_file.read().replace('\n', '').split(';')[:-1]:
                expression, parameters = string.split(' = ')
                params = json.loads(parameters)
                text_char = QTextCharFormat()
                for parameter in params.keys():
                    match parameter:
                        case 'foreground':
                            text_char.setForeground(QColor(*params['foreground']))
                        case 'background':
                            text_char.setBackground(QColor(*params['background']))
                        case 'weight':
                            text_char.setFontWeight(int(params['weight']))
                        case 'italic':
                            text_char.setFontItalic(bool(params['italic']))
                        case 'underline':
                            text_char.setFontUnderline(bool(params['underline']))
                        case 'underline_color':
                            text_char.setUnderlineColor(QColor(*params['underline_color']))
                        case 'underline_style':
                            text_char.setUnderlineStyle(int(params['underline_style']))
                self._mapping[rf'{expression}'] = text_char

    def highlightBlock(self, text: str) -> None:
        for pattern, char in self._mapping.items():
            for match in re.finditer(pattern, text):
                s, e = match.span()
                self.setFormat(s, e - s, char)


class EditorTab(QTextEdit):
    def __init__(self, filename: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename: str = filename
        with open(filename) as cf:
            self.setText(cf.read())
        self.saved_text: str = self.toPlainText()
        self.highlighter = None
        self.language = None

    def setHighlighter(self, highlighter: Highlighter):
        self.highlighter = highlighter
        self.highlighter.setDocument(self.document())

    def save(self) -> None:
        with open(self.filename, 'w') as sf:
            sf.write(self.toPlainText())
        self.saved_text = self.toPlainText()


class IdeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Vcode')
        self.resize(1000, 700)

        self.process = subprocess.Popen('python -V')
        self.process.wait()

        self.settings = QSettings('Vcode', 'Settings')

        self.settings_window = SettingsDialog(self)
        for st in STYLE.keys():
            st_rb: QRadioButton = QRadioButton(st, self)
            if st == self.settings.value('Style'):
                st_rb.setChecked(True)
            st_rb.clicked.connect(lambda: self.select_style(self.sender().text()))
            self.settings_window.style_select_layout.addWidget(st_rb)
        self.settings_window.language.currentTextChanged.connect(
            lambda: self.select_language(self.settings_window.language.currentText().lower()))

        self.settings_window.autorun.setChecked(bool(self.settings.value('Autorun')))
        self.settings_window.autorun.stateChanged.connect(self.autorun_check)

        self.settings_window.autosave.setChecked(bool(self.settings.value('Autosave')))
        self.settings_window.autosave.stateChanged.connect(
            lambda: self.settings.setValue('Autosave', int(self.settings_window.autosave.isChecked())))

        self.editor_tabs = QTabWidget(self)
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.editor_tabs)

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

        self.settings_btn = QAction(self)
        self.settings_btn.triggered.connect(self.settings_window.exec)
        self.file_menu.addAction(self.settings_btn)

        self.start_btn = QAction(self)
        self.start_btn.setShortcut(QKeySequence.StandardKey.Refresh)
        self.start_btn.triggered.connect(self.start_program)
        self.menuBar().addAction(self.start_btn)

        self.exit_btn = QAction(self)
        self.exit_btn.setShortcut(QKeySequence.StandardKey.Close)
        self.exit_btn.triggered.connect(self.close)
        self.menuBar().addAction(self.exit_btn)

        if len(self.settings.allKeys()) == 5:
            self.select_language(self.settings.value('Language'))
            self.select_style(self.settings.value('Style'))
        else:
            self.settings.setValue('Autorun', 0)
            self.settings.setValue('Autosave', 0)
            if 'JetBrains Mono' in QFontDatabase.families():
                self.settings.setValue('Font', QFont('JetBrains Mono', 12))
            else:
                self.settings.setValue('Font', QFont('Consolas', 12))
            self.select_language('en')
            self.select_style('Classic')

    def add_tab(self, filename):
        editor = EditorTab(filename, self)
        editor.textChanged.connect(self.auto_save)
        editor.setFont(self.settings.value('Font'))
        for lang, r in languages.items():
            if filename.rsplit('.', maxsplit=1)[-1] in r:
                editor.setHighlighter(Highlighter(f'highlights/{lang}.hl'))
                editor.language = lang
        self.editor_tabs.addTab(editor, filename)

    def close_tab(self, tab):
        if self.editor_tabs.currentWidget().saved_text != self.editor_tabs.currentWidget().toPlainText():
            button = QMessageBox.warning(
                self, 'Warning', 'Do you want to save changes?',
                buttons=QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
                defaultButton=QMessageBox.StandardButton.Save)
            if button == QMessageBox.StandardButton.Cancel:
                return
            else:
                self.editor_tabs.currentWidget().save_file()
        self.editor_tabs.removeTab(tab)

    def select_language(self, language):
        self.settings.setValue('Language', language)

        self.settings_window.setWindowTitle(texts.settings_window[language])
        self.file_menu.setTitle(texts.file_menu[language])
        self.open_btn.setText(texts.open_btn[language])
        self.save_as_btn.setText(texts.save_as_btn[language])
        self.settings_btn.setText(texts.settings_btn[language])
        self.start_btn.setText(texts.start_btn[language])
        self.exit_btn.setText(texts.exit_btn[language])

        self.settings_window.autorun.setText(texts.autorun[language])
        self.settings_window.autosave.setText(texts.autosave[language])

    def select_style(self, style_name):
        if style_name in STYLE.keys():
            self.settings.setValue('Style', style_name)
            self.setStyleSheet(STYLE[style_name])

    def autorun_check(self):
        self.settings.setValue('Autorun', int(self.settings_window.autorun.isChecked()))
        set_autorun(self.settings_window.autorun.isChecked())

    def start_program(self):
        if self.editor_tabs.count():
            if not self.settings.value('Autosave') and \
                    self.editor_tabs.currentWidget().saved_text != self.editor_tabs.currentWidget().toPlainText():
                button = QMessageBox.warning(
                    self, 'Warning', 'Do you want to save changes?',
                    buttons=QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
                    defaultButton=QMessageBox.StandardButton.Save)
                if button == QMessageBox.StandardButton.Cancel:
                    return
                else:
                    self.editor_tabs.currentWidget().save_file()
            self.process.terminate()
            threading.Thread(target=self.program).start()

    def program(self):
        code: EditorTab = self.editor_tabs.currentWidget()
        if code.language:
            self.process = subprocess.Popen(start_command[code.language].format(filename=code.filename))
            print(f'\033[1m\033[93mExit code: {self.process.wait()}\033[0m\n')
        else:
            print(f'\033[1m\033[93mCan`t start "{code.filename}"\033[0m\n')

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName()
        if file:
            self.add_tab(file)

    def save_as(self):
        path, _ = QFileDialog.getOpenFileName()
        if path:
            with open(path, 'w') as sf:
                sf.write(self.editor_tabs.currentWidget().toPlainText())

    def auto_save(self):
        if self.settings.value('Autosave'):
            self.editor_tabs.currentWidget().saved_text = self.editor_tabs.currentWidget().toPlainText()
            self.editor_tabs.currentWidget().save()

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.process.returncode is None:
            button = QMessageBox.warning(
                self, 'Warning', 'Do you want to terminate process?',
                buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                defaultButton=QMessageBox.StandardButton.Ok)
            if button == QMessageBox.StandardButton.Cancel:
                a0.ignore()
            else:
                self.process.terminate()
        for tab in self.editor_tabs.findChildren(EditorTab):
            if tab.saved_text != tab.toPlainText():
                button = QMessageBox.warning(
                    self, 'Warning', 'Do you want to save changes in file {}?'.format(tab.filename),
                    buttons=QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard |
                            QMessageBox.StandardButton.Cancel,
                    defaultButton=QMessageBox.StandardButton.Save)
                if button == QMessageBox.StandardButton.Cancel:
                    a0.ignore()
                elif button == QMessageBox.StandardButton.Save:
                    tab.save()
                    a0.accept()
                else:
                    a0.accept()


class SettingsDialog(QDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setModal(True)

        self.style_select: QGroupBox = QGroupBox(self)
        self.style_select_layout: QVBoxLayout = QVBoxLayout()
        self.style_select.setLayout(self.style_select_layout)

        self.language: QComboBox = QComboBox(self)
        self.language.addItems(['EN', 'RU', 'DE'])

        self.wgt: QWidget = QWidget()
        self.lay: QVBoxLayout = QVBoxLayout()
        self.wgt.setLayout(self.lay)

        self.autorun: QCheckBox = QCheckBox(self)
        self.lay.addWidget(self.autorun)

        self.autosave: QCheckBox = QCheckBox(self)
        self.lay.addWidget(self.autosave)

        self.m_lay: QGridLayout = QGridLayout(self)
        self.m_lay.addWidget(self.style_select, 0, 0, 1, 1)
        self.m_lay.addWidget(self.wgt, 0, 1, 2, 1)
        self.m_lay.addWidget(self.language, 1, 0, 1, 1)
        self.setLayout(self.m_lay)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IdeWindow()
    ide.show()
    sys.exit(app.exec())
