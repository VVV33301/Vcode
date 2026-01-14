from PyQt6.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QFileDialog
from PyQt6.QtCore import QSettings, Qt
import json
import texts
from .lineedit import LineEditMenu


class ProjectSettingsDialog(QDialog):
    """Settings of project"""

    def __init__(self, project: dict[str, str], path, parent, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setMinimumSize(400, 250)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.parent = parent
        layout: QGridLayout = QGridLayout(self)
        self.setLayout(layout)
        self.lang_s: str = QSettings('Vcode', 'Settings').value('Language')

        self.project: dict[str, str] = project
        self.path: str = path
        self.setWindowTitle(project['name'] + ' - ' + texts.settings_btn[self.lang_s])

        self.name: QLineEdit = QLineEdit(self.project['name'], self)
        self.name.setPlaceholderText('Name')
        self.name.contextMenuEvent = LineEditMenu(self.name)
        layout.addWidget(self.name, 0, 0, 1, 2)

        # self.file_formats: QLineEdit = QLineEdit(' '.join(language_list[self.language]['file_formats']), self)
        # self.file_formats.setPlaceholderText('Supported file formats')
        # self.file_formats.contextMenuEvent = LineEditMenu(self.file_formats)
        # layout.addWidget(self.file_formats, 1, 0, 1, 2)

        self.start_command: QLineEdit = QLineEdit(self.project.get('start_command', ''), self)
        self.start_command.setPlaceholderText('Start command')
        self.start_command.contextMenuEvent = LineEditMenu(self.start_command)
        layout.addWidget(self.start_command, 1, 0, 1, 2)

        self.debug_command: QLineEdit = QLineEdit(self.project.get('debug_command', ''), self)
        self.debug_command.setPlaceholderText('Debug command')
        self.debug_command.contextMenuEvent = LineEditMenu(self.debug_command)
        layout.addWidget(self.debug_command, 2, 0, 1, 2)

        self.find_start: QPushButton = QPushButton(texts.find_start_btn[self.lang_s], self)
        self.find_start.clicked.connect(self.find_compiler)
        layout.addWidget(self.find_start, 3, 0, 1, 1)

        self.find_debug: QPushButton = QPushButton(texts.find_debug_btn[self.lang_s], self)
        self.find_debug.clicked.connect(self.find_debugger)
        layout.addWidget(self.find_debug, 3, 1, 1, 1)

        self.save_btn: QPushButton = QPushButton(texts.save_btn[self.lang_s], self)
        self.save_btn.clicked.connect(self.save_language)
        layout.addWidget(self.save_btn, 4, 0, 1, 2)

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

    def save_language(self) -> None:
        """Save a language"""
        new_lang_settings: dict[str, str] = {
            'name': self.name.text(),
            'start_command': self.start_command.text(),
            'debug_command': self.debug_command.text(),
            'git': self.project.get('git', 'false')
        }
        with open(self.path + '/.vcodeproject', 'w') as h:
            json.dump(new_lang_settings, h)
        self.parent.restart()
        self.accept()
