import sys
import os
import subprocess
import threading
import re
import json
from winreg import HKEYType, HKEY_CURRENT_USER, KEY_ALL_ACCESS, REG_SZ, OpenKey, SetValueEx, DeleteValue
from webbrowser import open as openweb

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import texts
from style import STYLE

PATH: str = os.getcwd()
with open('languages.json') as llf:
    language_list: dict = json.load(llf)
filters: list = ['All Files (*.*)']
for i, j in language_list.items():
    filters.append(f'{i} Files (*.{" *.".join(j["file_formats"])})')


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


class TextEditMenu(QMenu):
    """Custom QLineEdit with new QMenu"""
    def __init__(self, parent: QTextEdit, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.p: QTextEdit = parent

        self.undo: QAction = QAction(self)
        self.undo.triggered.connect(self.p.undo)
        self.undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.addAction(self.undo)

        self.redo: QAction = QAction(self)
        self.redo.triggered.connect(self.p.redo)
        self.redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.addAction(self.redo)

        self.addSeparator()

        self.cut: QAction = QAction(self)
        self.cut.triggered.connect(self.p.cut)
        self.cut.setShortcut(QKeySequence.StandardKey.Cut)
        self.addAction(self.cut)

        self.copy: QAction = QAction(self)
        self.copy.triggered.connect(self.p.copy)
        self.copy.setShortcut(QKeySequence.StandardKey.Copy)
        self.addAction(self.copy)

        self.paste: QAction = QAction(self)
        self.paste.triggered.connect(self.p.paste)
        self.paste.setShortcut(QKeySequence.StandardKey.Paste)
        self.addAction(self.paste)

        self.select_all: QAction = QAction(self)
        self.select_all.triggered.connect(self.p.selectAll)
        self.select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.addAction(self.select_all)

        self.addSeparator()

        self.start: QAction = QAction(self)
        self.start.triggered.connect(ide.start_program)
        self.start.setShortcut(QKeySequence.StandardKey.Refresh)
        self.addAction(self.start)

    def __call__(self, event: QContextMenuEvent) -> None:
        """Call this class to get contect menu"""
        lang: str = ide.settings.value('language')
        self.undo.setText(texts.undo[lang])
        self.redo.setText(texts.redo[lang])
        self.cut.setText(texts.cut[lang])
        self.copy.setText(texts.copy[lang])
        self.paste.setText(texts.paste[lang])
        self.select_all.setText(texts.select_all[lang])
        self.start.setText(texts.start_btn[lang])
        self.popup(event.globalPos())


class EditorTab(QTextEdit):
    def __init__(self, file: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file: str = file.replace('\\', '/')
        self.filename: str = file.split('/')[-1]
        with open(file, encoding='utf-8') as cf:
            self.setText(cf.read())
        self.saved_text: str = self.toPlainText()
        self.highlighter: Highlighter | None = None
        self.start_command: str | None = None
        self.language: str = ''

    def setHighlighter(self, highlighter: Highlighter):
        self.highlighter = highlighter
        self.highlighter.setDocument(self.document())

    def save(self) -> None:
        with open(self.file, 'w', encoding='utf-8') as sf:
            sf.write(self.toPlainText())
        self.saved_text = self.toPlainText()


class IdeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Vcode')

        self.process: subprocess.Popen | None = None

        self.settings: QSettings = QSettings('Vcode', 'Settings')

        self.about_window: AboutDialog = AboutDialog(self)

        self.settings_window: SettingsDialog = SettingsDialog(self)
        for st in STYLE.keys():
            st_rb: QRadioButton = QRadioButton(st, self)
            if st == self.settings.value('Style'):
                st_rb.setChecked(True)
            st_rb.clicked.connect(lambda: self.select_style(self.sender().text()))
            self.settings_window.style_select_layout.addWidget(st_rb)

        self.editor_tabs: QTabWidget = QTabWidget(self)
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)

        self.model = QFileSystemModel(self)
        self.model.setRootPath('')
        self.model.setFilter(QDir.Filter.Hidden | QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Files)
        self.tree = QTreeView(self)
        self.tree.setMinimumWidth(100)
        self.tree.setModel(self.model)
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.doubleClicked.connect(lambda x: self.add_tab(self.model.filePath(x)))

        self.splitter = QSplitter()
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.editor_tabs)
        self.splitter.setSizes([150, 500])
        self.setCentralWidget(self.splitter)

        self.file_menu: QMenu = QMenu(self)
        self.menuBar().addMenu(self.file_menu)

        self.new_btn: QAction = QAction(self)
        self.new_btn.setShortcut(QKeySequence.StandardKey.New)
        self.new_btn.triggered.connect(self.new_file)
        self.file_menu.addAction(self.new_btn)

        self.open_btn: QAction = QAction(self)
        self.open_btn.setShortcut(QKeySequence.StandardKey.Open)
        self.open_btn.triggered.connect(self.open_file)
        self.file_menu.addAction(self.open_btn)

        self.save_btn: QAction = QAction(self)
        self.save_btn.setShortcut(QKeySequence.StandardKey.Save)
        self.save_btn.triggered.connect(lambda: self.editor_tabs.currentWidget().save())
        self.file_menu.addAction(self.save_btn)

        self.save_as_btn: QAction = QAction(self)
        self.save_as_btn.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_btn.triggered.connect(self.save_as)
        self.file_menu.addAction(self.save_as_btn)

        self.settings_btn: QAction = QAction(self)
        self.settings_btn.triggered.connect(self.settings_window.exec)
        self.menuBar().addAction(self.settings_btn)

        self.start_btn: QAction = QAction(self)
        self.start_btn.setShortcut(QKeySequence.StandardKey.Refresh)
        self.start_btn.triggered.connect(self.start_program)
        self.menuBar().addAction(self.start_btn)

        self.about_menu: QAction = QMenu(self)
        self.menuBar().addMenu(self.about_menu)

        self.about_btn: QAction = QAction(self)
        self.about_btn.triggered.connect(self.about_window.exec)
        self.about_menu.addAction(self.about_btn)

        self.feedback_btn: QAction = QAction(self)
        self.feedback_btn.triggered.connect(lambda: openweb('https://forms.gle/Y21dgoB7ehy3hJjD6'))
        self.about_menu.addAction(self.feedback_btn)

        self.exit_btn: QAction = QAction(self)
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

        self.settings_window.language.setCurrentText(self.settings.value('Language').upper())
        self.settings_window.language.currentTextChanged.connect(
            lambda: self.select_language(self.settings_window.language.currentText().lower()))

        self.settings_window.autorun.setChecked(bool(self.settings.value('Autorun')))
        self.settings_window.autorun.stateChanged.connect(self.autorun_check)

        self.settings_window.autosave.setChecked(bool(self.settings.value('Autosave')))
        self.settings_window.autosave.stateChanged.connect(
            lambda: self.settings.setValue('Autosave', int(self.settings_window.autosave.isChecked())))

        self.settings_window.fonts.setCurrentText(self.settings.value('Font').family())
        self.settings_window.fonts.currentTextChanged.connect(
            lambda: self.settings.setValue('Font', QFont(self.settings_window.fonts.currentText(), 12)))

    def add_tab(self, filename):
        for tab in self.editor_tabs.findChildren(EditorTab):
            if tab.file == filename:
                self.editor_tabs.setCurrentWidget(tab)
                return
        editor: EditorTab = EditorTab(filename, self)
        editor.textChanged.connect(self.auto_save)
        editor.setFont(self.settings.value('Font'))
        editor.contextMenuEvent = TextEditMenu(editor)
        for langname, language in language_list.items():
            if filename.rsplit('.', maxsplit=1)[-1] in language['file_formats']:
                editor.setHighlighter(Highlighter('{}/highlights/{lang}'.format(PATH, lang=language['highlight'])))
                editor.start_command = language['start_command']
                editor.language = langname
        i = self.editor_tabs.addTab(editor, editor.filename)
        self.editor_tabs.setCurrentIndex(i)

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
        self.new_btn.setText(texts.new_btn[language])
        self.open_btn.setText(texts.open_btn[language])
        self.save_btn.setText(texts.save_btn[language])
        self.save_as_btn.setText(texts.save_as_btn[language])
        self.settings_btn.setText(texts.settings_btn[language])
        self.start_btn.setText(texts.start_btn[language])
        self.about_menu.setTitle(texts.about_menu[language])
        self.about_btn.setText(texts.about_btn[language])
        self.feedback_btn.setText(texts.feedback_btn[language])
        self.exit_btn.setText(texts.exit_btn[language])

        self.settings_window.autorun.setText(texts.autorun[language])
        self.settings_window.autosave.setText(texts.autosave[language])
        self.settings_window.style_select_group.setTitle(texts.style_select_group[language])

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
            if self.process:
                self.process.terminate()
            threading.Thread(target=self.program).start()

    def program(self):
        code: EditorTab = self.editor_tabs.currentWidget()
        if code.language in language_list.keys():
            self.process = subprocess.Popen(code.start_command.format(filename=code.file))
            print(f'\033[1m\033[93mExit code: {self.process.wait()}\033[0m\n')
        else:
            print(f'\033[1m\033[93mCan`t start "{code.filename}"\033[0m\n')

    def new_file(self):
        file, _ = QFileDialog.getSaveFileName(directory='untitled', filter=';;'.join(filters))
        if file:
            open(file, 'w', encoding='utf-8').close()
            self.add_tab(file)

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
        if self.process and self.process.returncode is None:
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

        self.style_select_group: QGroupBox = QGroupBox(self)
        self.style_select_layout: QVBoxLayout = QVBoxLayout()
        self.style_select_group.setLayout(self.style_select_layout)

        self.language: QComboBox = QComboBox(self)
        self.language.addItems(['EN', 'RU', 'DE'])

        self.fonts: QComboBox = QComboBox(self)
        self.fonts.addItems(QFontDatabase.families())

        self.check_boxes_group: QGroupBox = QGroupBox(self)
        self.check_boxes_layout: QVBoxLayout = QVBoxLayout()
        self.check_boxes_group.setLayout(self.check_boxes_layout)

        self.autorun: QCheckBox = QCheckBox(self)
        self.check_boxes_layout.addWidget(self.autorun)

        self.autosave: QCheckBox = QCheckBox(self)
        self.check_boxes_layout.addWidget(self.autosave)

        self.m_lay: QGridLayout = QGridLayout(self)
        self.m_lay.addWidget(self.style_select_group, 0, 0, 1, 1)
        self.m_lay.addWidget(self.check_boxes_group, 0, 1, 1, 1)
        self.m_lay.addWidget(self.language, 1, 0, 1, 1)
        self.m_lay.addWidget(self.fonts, 1, 1, 1, 1)
        self.setLayout(self.m_lay)


class AboutDialog(QDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setModal(True)
        self.setWindowTitle('Vcode v0.1')
        self.setMinimumSize(250, 200)
        self.lay = QVBoxLayout()

        self.icon = QLabel(self)
        self.icon.setPixmap(QPixmap('Vcode.ico').scaled(128, 128))
        self.icon.resize(128, 128)
        self.lay.addWidget(self.icon, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.name = QLabel('Vcode', self)
        self.name.setFont(QFont('Arial', 18))
        self.lay.addWidget(self.name, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.text = QLabel('Version: 0.1.0', self)
        self.lay.addWidget(self.text)

        self.setLayout(self.lay)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('Vcode.ico'))
    ide = IdeWindow()
    ide.show()
    sys.exit(app.exec())
