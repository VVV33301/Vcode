from PyQt6.QtWidgets import QDialog, QGridLayout, QVBoxLayout, QPushButton
from PyQt6.QtCore import QSettings
from os.path import expanduser
from .highlightmakerstring import HighlightMakerString
import texts


class HighlightMaker(QDialog):
    """Make and rewrite highlights"""

    def __init__(self, highlighter: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setMinimumSize(300, 300)
        self.highlighter: str = highlighter
        layout: QGridLayout = QGridLayout(self)
        self.layout_hl: QVBoxLayout = QVBoxLayout()
        self.setLayout(layout)
        with open(highlighter) as hlf:
            for i in hlf.read().split(';')[:-1]:
                str_item: HighlightMakerString = HighlightMakerString(*i.split(' = '))
                str_item.remove_btn.clicked.connect(lambda: self.layout_hl.removeWidget(self.sender().parent()))
                self.layout_hl.addWidget(str_item)
        layout.addLayout(self.layout_hl, 0, 0, 1, 2)
        self.lang_s: QSettings = QSettings('Vcode', 'Settings')
        self.add_btn: QPushButton = QPushButton(texts.add_btn[self.lang_s.value('Language')], self)
        self.add_btn.clicked.connect(self.add_string)
        layout.addWidget(self.add_btn, 1, 0, 1, 1)
        self.save_btn: QPushButton = QPushButton(texts.save_btn[self.lang_s.value('Language')], self)
        self.save_btn.clicked.connect(self.save_highlighter)
        layout.addWidget(self.save_btn, 1, 1, 1, 1)
        if highlighter.startswith(expanduser('~') + '/.Vcode/highlights') and highlighter.endswith(
                ('python.hl', 'html.hl', 'json.hl')):
            self.default_btn: QPushButton = QPushButton(texts.default_btn[self.lang_s.value('Language')], self)
            self.default_btn.clicked.connect(self.default)
            layout.addWidget(self.default_btn, 2, 0, 1, 2)

    def add_string(self) -> None:
        """Add new string"""
        self.layout_hl.addWidget(HighlightMakerString('', '{}'))

    def save_highlighter(self) -> None:
        """Save highlighter to .hl file"""
        with open(self.highlighter, 'w') as hlf:
            for hms1 in self.findChildren(HighlightMakerString):
                hlf.write(hms1.rstring.text() + ' = {' + hms1.json_params.text() + '};\n')

    def default(self) -> None:
        """Set default highlighter"""
        if self.highlighter.endswith('python.hl'):
            from default import python_hl
            with open(self.highlighter, 'w') as hlf:
                hlf.write(python_hl)
        if self.highlighter.endswith('html.hl'):
            from default import html_hl
            with open(self.highlighter, 'w') as hlf:
                hlf.write(html_hl)
        if self.highlighter.endswith('json.hl'):
            from default import json_hl
            with open(self.highlighter, 'w') as hlf:
                hlf.write(json_hl)
        self.accept()
