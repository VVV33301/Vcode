from PyQt6.QtWidgets import QDialog, QGridLayout, QComboBox, QLineEdit, QPushButton, QFileDialog, QMainWindow
from PyQt6.QtCore import QSettings
import json
from default import USER
import texts
from .lineedit import LineEditMenu
from .highlightmaker import HighlightMaker
from .warning import WarningMessageBox
from ide import language_list


class ProjectSettingsDialog(QDialog):
    """Settings of programming languages"""

    def __init__(self, language: str, app: QMainWindow, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setMinimumSize(400, 250)
        self.language: str = language
        self.app: QMainWindow = app
        layout: QGridLayout = QGridLayout(self)
        self.setLayout(layout)
        self.lang_s: str = QSettings('Vcode', 'Settings').value('Language')
        hist: dict[str, list[str]] = json.loads(QSettings('Vcode', 'CompilerHistory').value(
            language, '{"start_command": [], "debug_command": []}'))

        self.highlight: QLineEdit = QLineEdit(language_list[self.language]['highlight'], self)
        self.highlight.setPlaceholderText('Highlight file path')
        self.highlight.contextMenuEvent = LineEditMenu(self.highlight)
        layout.addWidget(self.highlight, 0, 0, 1, 6)

        self.file_formats: QLineEdit = QLineEdit(' '.join(language_list[self.language]['file_formats']), self)
        self.file_formats.setPlaceholderText('Supported file formats')
        self.file_formats.contextMenuEvent = LineEditMenu(self.file_formats)
        layout.addWidget(self.file_formats, 1, 0, 1, 6)

        self.start_command: QComboBox = QComboBox(self)
        self.start_command.setObjectName('asline')
        self.start_command.addItem(language_list[self.language]['start_command'])
        self.start_command.setEditable(True)
        self.start_command.setPlaceholderText('Start command')
        self.start_command.contextMenuEvent = LineEditMenu(self.start_command.lineEdit())
        self.start_command.addItems(hist['start_command'])
        layout.addWidget(self.start_command, 2, 0, 1, 6)

        self.debug_command: QComboBox = QComboBox(self)
        self.debug_command.setObjectName('asline')
        self.debug_command.addItem(language_list[self.language]['debug_command'])
        self.debug_command.setEditable(True)
        self.debug_command.setPlaceholderText('Debug command')
        self.debug_command.contextMenuEvent = LineEditMenu(self.debug_command.lineEdit())
        self.debug_command.addItems(hist['debug_command'])
        layout.addWidget(self.debug_command, 3, 0, 1, 6)

        self.find_highlight: QPushButton = QPushButton(texts.find_highlight_btn[self.lang_s], self)
        self.find_highlight.clicked.connect(self.find_highlight_file)
        layout.addWidget(self.find_highlight, 4, 0, 1, 2)

        self.find_start: QPushButton = QPushButton(texts.find_start_btn[self.lang_s], self)
        self.find_start.clicked.connect(self.find_compiler)
        layout.addWidget(self.find_start, 4, 2, 1, 2)

        self.find_debug: QPushButton = QPushButton(texts.find_debug_btn[self.lang_s], self)
        self.find_debug.clicked.connect(self.find_debugger)
        layout.addWidget(self.find_debug, 4, 4, 1, 2)

        self.edit_highlight_btn: QPushButton = QPushButton(texts.edit_highlight_btn[self.lang_s], self)
        self.edit_highlight_btn.clicked.connect(self.highlight_maker_call)
        layout.addWidget(self.edit_highlight_btn, 5, 0, 1, 3)

        self.save_btn: QPushButton = QPushButton(texts.save_btn[self.lang_s], self)
        self.save_btn.clicked.connect(self.save_language)
        layout.addWidget(self.save_btn, 5, 3, 1, 3)

    def find_highlight_file(self):
        """Search highlight file in all files"""
        a, _ = QFileDialog.getOpenFileName(self, directory=USER, filter='Highlight files (*.hl)')
        if a:
            self.highlight.setText(a)

    def find_compiler(self):
        """Search compiler in files"""
        a, _ = QFileDialog.getOpenFileName(
            self, directory=USER, filter='Executable files (*.exe);;Shell files (*.sh *.bat *.vbs);;All files (*.*)')
        if a:
            self.start_command.insertItem(0, f'"{a}" "{{filename}}"')
            self.start_command.setCurrentIndex(0)

    def find_debugger(self):
        """Search debugger in files"""
        a, _ = QFileDialog.getOpenFileName(
            self, directory=USER, filter='Executable files (*.exe);;Shell files (*.sh *.bat *.vbs);;All files (*.*)')
        if a:
            self.start_command.insertItem(0, f'"{a}" "{{filename}}"')
            self.start_command.setCurrentIndex(0)

    def highlight_maker_call(self) -> None:
        """Start highlight maker"""
        if not language_list[self.language]['highlight']:
            with open(USER + './Vcode/highlights/' + self.language.lower() + '.hl', 'w') as hn:
                hn.write('[A-Za-z0-9]+ = {"foreground": [127, 127, 127]};')
            language_list[self.language]['highlight'] = USER + './Vcode/highlights/' + self.language.lower() + '.hl'
        hlm: HighlightMaker = HighlightMaker(language_list[self.language]['highlight'], self)
        hlm.setWindowTitle(f'{language_list[self.language]["highlight"].split("/")[-1]} - Vcode highlight maker')
        hlm.exec()

    def save_language(self) -> None:
        """Save a language"""
        new_lang_settings: dict[str, str] = {'highlight': self.highlight.text(),
                                             'file_formats': [f for f in self.file_formats.text().split()],
                                             'start_command': self.start_command.currentText(),
                                             'debug_command': self.debug_command.currentText()}
        if new_lang_settings != language_list[self.language]:
            language_list[self.language] = new_lang_settings
            with open(USER + '/.Vcode/languages.json', 'w') as llfw:
                json.dump(language_list, llfw)
            QSettings('Vcode', 'CompilerHistory').setValue(self.language, json.dumps({
                'start_command': list(set(self.start_command.itemText(i) for i in range(self.start_command.count()))),
                'debug_command': list(set(self.debug_command.itemText(i) for i in range(self.debug_command.count())))}))
            rst: str = WarningMessageBox(self, 'Reset', texts.restart_warning, WarningMessageBox.RESTART).wait()
            if rst == texts.restart_btn[self.lang_s]:
                self.app.restart()
        self.accept()
