from PyQt6.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QFileDialog, QMainWindow
from PyQt6.QtCore import QSettings, Qt
import json
from default import CONFIG_PATH
import texts
from .lineedit import LineEditMenu
from .highlightmaker import HighlightMaker
from .warning import WarningMessageBox


class ProjectSettingsDialog(QDialog):
    """Settings of project"""

    def __init__(self, project: dict[str, str], parent, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setMinimumSize(400, 250)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.parent = parent
        layout: QGridLayout = QGridLayout(self)
        self.setLayout(layout)
        self.lang_s: str = QSettings('Vcode', 'Settings').value('Language')

        self.project: dict[str, str] = project
        self.setWindowTitle(project['name'] + ' - ' + texts.settings_btn[self.lang_s])

        self.name: QLineEdit = QLineEdit(self.project['name'], self)
        self.name.setPlaceholderText('Name')
        self.name.contextMenuEvent = LineEditMenu(self.name)
        layout.addWidget(self.name, 0, 0, 1, 6)

        self.highlight: QLineEdit = QLineEdit(self.project['highlight'], self)
        self.highlight.setPlaceholderText('Highlight file path')
        self.highlight.contextMenuEvent = LineEditMenu(self.highlight)
        layout.addWidget(self.highlight, 1, 0, 1, 6)

        # self.file_formats: QLineEdit = QLineEdit(' '.join(language_list[self.language]['file_formats']), self)
        # self.file_formats.setPlaceholderText('Supported file formats')
        # self.file_formats.contextMenuEvent = LineEditMenu(self.file_formats)
        # layout.addWidget(self.file_formats, 1, 0, 1, 6)

        self.start_command: QLineEdit = QLineEdit(self.project['start_command'], self)
        self.start_command.setPlaceholderText('Start command')
        self.start_command.contextMenuEvent = LineEditMenu(self.start_command)
        layout.addWidget(self.start_command, 2, 0, 1, 6)

        self.debug_command: QLineEdit = QLineEdit(self.project['debug_command'], self)
        self.debug_command.setPlaceholderText('Debug command')
        self.debug_command.contextMenuEvent = LineEditMenu(self.debug_command)
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
        a, _ = QFileDialog.getOpenFileName(self, directory=CONFIG_PATH, filter='Highlight files (*.hl)')
        if a:
            self.highlight.setText(a)

    def find_compiler(self):
        """Search compiler in files"""
        a, _ = QFileDialog.getOpenFileName(
            self, directory='%AppData%',
            filter='Executable files (*.exe);;Shell files (*.sh *.bat *.vbs);;All files (*.*)')
        if a:
            self.start_command.setText(f'"{a}" "{{filename}}"')

    def find_debugger(self):
        """Search debugger in files"""
        a, _ = QFileDialog.getOpenFileName(
            self, directory='%AppData%',
            filter='Executable files (*.exe);;Shell files (*.sh *.bat *.vbs);;All files (*.*)')
        if a:
            self.debug_command.setText(f'"{a}" "{{filename}}"')

    def highlight_maker_call(self) -> None:
        """Start highlight maker"""
        if not self.project['highlight']:
            with open(CONFIG_PATH + '/highlights/' + self.project['name'] + '.hl', 'w') as hn:
                hn.write('[A-Za-z0-9]+ = {"foreground": [127, 127, 127]};')
            self.project['highlight'] = CONFIG_PATH + '/highlights/' + self.project['name'] + '.hl'
        hlm: HighlightMaker = HighlightMaker(self.project['highlight'], self)
        hlm.setWindowTitle(f'{self.project["highlight"].split("/")[-1]} - Vcode highlight maker')
        hlm.exec()

    def save_language(self) -> None:
        """Save a language"""
        new_lang_settings: dict[str, str] = {
            'path': self.project['path'],
            'name': self.name.text(),
            'highlight': self.highlight.text(),
            'start_command': self.start_command.text(),
            'debug_command': self.debug_command.text(),
            'git': self.project['git']
        }
        with open(self.project['path'] + '/.vcodeproject', 'w') as h:
            json.dump(new_lang_settings, h)
        rst: str = WarningMessageBox(self, 'Reset', texts.restart_warning, WarningMessageBox.RESTART).wait()
        if rst == texts.restart_btn[self.lang_s]:
            self.parent.restart()
        self.accept()
