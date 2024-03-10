# Vcode
# Copyright (C) 2023-2024  Vladimir Varenik  <feedback.vcode@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see https://www.gnu.org/licenses/.


import sys
import subprocess
import threading
import re
import json
import shutil
from webbrowser import open as openweb
from os import mkdir, system, remove, getpid, rename, startfile, listdir
from os.path import isfile, isdir, dirname, abspath, join, exists
from requests import get
import psutil

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import texts
from default import USER, ENCODINGS

try:
    import git
    GIT_INSTALLED: bool = True
except ImportError:
    git = None
    GIT_INSTALLED: bool = False

VERSION: str = '0.6.2'


def resource_path(relative_path: str) -> str:
    """Return absolute path of file"""
    return join(getattr(sys, '_MEIPASS', dirname(abspath(sys.argv[0]))), relative_path)


def set_autorun(enabled: bool) -> None:
    """Set program autorun on start operating system (only for Windows)"""
    if sys.platform == 'win32':
        from winreg import HKEYType, HKEY_CURRENT_USER, KEY_ALL_ACCESS, REG_SZ, OpenKey, SetValueEx, DeleteValue
        key: HKEYType = OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                                0, KEY_ALL_ACCESS)
        if enabled:
            SetValueEx(key, 'Vcode', 0, REG_SZ, sys.argv[0])
        else:
            DeleteValue(key, 'Vcode')
        key.Close()


def update_filters() -> list[str]:
    """Add filters for file searching"""
    filters_f: list = ['All Files (*.*)']
    for i, j in language_list.items():
        filters_f.append(f'{i} Files (*.{" *.".join(j["file_formats"])})')
    return filters_f


style: dict[str, str] = {}
for file in listdir(resource_path('styles')):
    if isfile(resource_path('styles/' + file)) and file.endswith('.qss'):
        with open(resource_path('styles/' + file)) as qss:
            style[file[:-4]] = qss.read()

if exists(USER + '/.Vcode/languages.json'):
    with open(USER + '/.Vcode/languages.json') as llf:
        language_list: dict[str, dict[str, str]] = json.load(llf)
    if 'Python' not in language_list.keys():
        from default import python_ll
        language_list["Python"] = python_ll
        with open(USER + '/.Vcode/languages.json', 'w') as llf:
            json.dump(language_list, llf)
    if 'Html' not in language_list.keys():
        from default import html_ll
        language_list["Html"] = html_ll
        with open(USER + '/.Vcode/languages.json', 'w') as llf:
            json.dump(language_list, llf)
    if 'JSON' not in language_list.keys():
        from default import json_ll
        language_list["JSON"] = json_ll
        with open(USER + '/.Vcode/languages.json', 'w') as llf:
            json.dump(language_list, llf)
else:
    from default import python_ll, html_ll, json_ll, python_hl, html_hl, json_hl
    language_list: dict[str, dict[str, str]] = {"Python": python_ll, "Html": html_ll, "JSON": json_ll}
    if not exists(USER + '/.Vcode/'):
        mkdir(USER + '/.Vcode/')
    with open(USER + '/.Vcode/languages.json', 'w') as llf:
        json.dump(language_list, llf)
    if not exists(USER + '/.Vcode/highlights/'):
        mkdir(USER + '/.Vcode/highlights/')
    with open(USER + '/.Vcode/highlights/python.hl', 'w') as llf:
        llf.write(python_hl)
    with open(USER + '/.Vcode/highlights/html.hl', 'w') as llf:
        llf.write(html_hl)
    with open(USER + '/.Vcode/highlights/json.hl', 'w') as llf:
        llf.write(json_hl)
if 'debug_command' not in language_list['Python'].keys():
    from default import python_ll, html_ll, json_ll
    language_list['Python']['debug_command'] = python_ll['debug_command']
    language_list['Html']['debug_command'] = html_ll['debug_command']
    language_list['JSON']['debug_command'] = json_ll['debug_command']
    with open(USER + '/.Vcode/languages.json', 'w') as llf:
        json.dump(language_list, llf)


class Highlighter(QSyntaxHighlighter):
    """Highlighter for code"""

    def __init__(self, highlight_path: str, parent: QTextDocument | None = None) -> None:
        super().__init__(parent)
        self.path: str = highlight_path
        self.mapping: dict[str, QTextCharFormat] = {}
        self.tab_words: list[str] = []
        self.complete_words: list[str] = []
        with open(highlight_path) as highlight_file:
            for string in highlight_file.read().replace('\n', '').split(';')[:-1]:
                expression, parameters = string.rsplit(' = ', maxsplit=1)
                params: dict[str, str] = json.loads(parameters)
                text_char: QTextCharFormat = QTextCharFormat()
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
                            text_char.setUnderlineStyle(QTextCharFormat.UnderlineStyle(int(params['underline_style'])))
                        case 'tab':
                            if params['tab'] == 1:
                                for i in expression.split('|'):
                                    self.tab_words.append(i)
                        case 'complete':
                            if params['complete'] == 1:
                                for i in expression.split('|'):
                                    self.complete_words.append(i)
                self.mapping[rf'{expression}']: QTextCharFormat = text_char

    def highlightBlock(self, text: str) -> None:
        """Highlight the block of text"""
        for pattern, char in self.mapping.items():
            for match in re.finditer(pattern, text, re.MULTILINE):
                s, e = match.span()
                self.setFormat(s, e - s, char)


class InputDialog(QDialog):
    """Custom QInputDialog"""

    def __init__(self, title: str, text: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle(title)
        self.l: QVBoxLayout = QVBoxLayout(self)
        self.l.addWidget(QLabel(text, self))
        self.le: QLineEdit = QLineEdit(self)
        self.le.contextMenuEvent = LineEditMenu(self.le)
        self.l.addWidget(self.le)
        self.ok_btn: QPushButton = QPushButton('OK', self)
        self.ok_btn.clicked.connect(self.accept)
        self.l.addWidget(self.ok_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def text_value(self) -> str:
        """Returns entered text"""
        return self.le.text()


class WarningMessageBox(QMessageBox):
    """Custom QMessageBox"""
    INFO: int = 0
    SAVE: int = 1
    UPDATE: int = 2

    def __init__(self, parent: QWidget, title: str, text_all_lang: dict[str, str],
                 msg_type: int = INFO) -> None:
        super().__init__(parent=parent)
        lang: str = QSettings('Vcode', 'Settings').value('Language')
        self.setWindowTitle(title)
        self.setText(text_all_lang[lang])

        if msg_type == self.SAVE:
            self.setStandardButtons(self.StandardButton.Save | self.StandardButton.Discard | self.StandardButton.Cancel)
            self.setDefaultButton(self.StandardButton.Save)
            self.button(self.StandardButton.Save).setText(texts.save_btn[lang])
            self.button(self.StandardButton.Discard).setText(texts.discard_btn[lang])
            self.button(self.StandardButton.Cancel).setText(texts.cancel_btn[lang])
        elif msg_type == self.UPDATE:
            self.setStandardButtons(self.StandardButton.Yes | self.StandardButton.No)
            self.setDefaultButton(self.StandardButton.Yes)
            self.button(self.StandardButton.Yes).setText(texts.update_btn[lang])
            self.button(self.StandardButton.No).setText(texts.cancel_btn[lang])
        else:
            self.setStandardButtons(self.StandardButton.Ok)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def wait(self) -> str:
        """Start GUI, wait exit and return clicked button"""
        self.exec()
        return self.clickedButton().text()


class TextEditMenu(QMenu):
    """Custom QTextEdit Menu"""

    def __init__(self, parent: QTextEdit | QPlainTextEdit, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self.p: QTextEdit | QPlainTextEdit = parent

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

        self.find: QAction = QAction(self)
        self.find.triggered.connect(lambda: FindWindow(self.p).exec())
        self.find.setShortcut(QKeySequence.StandardKey.Find)
        self.addAction(self.find)

        self.addSeparator()

        self.start: QAction = QAction(self)
        self.start.triggered.connect(lambda: ide.start_program(file_ed=self.p))
        self.start.setShortcut('F5')
        self.addAction(self.start)

        self.debug: QAction = QAction(self)
        self.debug.triggered.connect(lambda: ide.debug_program(file_ed=self.p))
        self.debug.setShortcut('Shift+F5')
        self.addAction(self.debug)

        self.addSeparator()

        self.search: QMenu = QMenu(self)
        self.addMenu(self.search)

        self.search_in_g: QAction = QAction(self)
        self.search_in_g.triggered.connect(
            lambda: openweb(f'https://www.google.com/search?q={self.p.textCursor().selectedText()}'))
        self.search.addAction(self.search_in_g)

        self.search_in_so: QAction = QAction(self)
        self.search_in_so.triggered.connect(
            lambda: openweb(f'https://stackoverflow.com/search?q={self.p.textCursor().selectedText()}'))
        self.search.addAction(self.search_in_so)

        self.lang_s: QSettings = QSettings('Vcode', 'Settings')

    def __call__(self, event: QContextMenuEvent) -> None:
        lang: str = self.lang_s.value('Language')
        self.undo.setText(texts.undo[lang])
        self.redo.setText(texts.redo[lang])
        self.cut.setText(texts.cut[lang])
        self.copy.setText(texts.copy[lang])
        self.paste.setText(texts.paste[lang])
        self.select_all.setText(texts.select_all[lang])
        self.find.setText(texts.find_btn[lang])
        self.start.setText(texts.start_btn[lang])
        self.debug.setText(texts.debug_btn[lang])
        self.search.setTitle(texts.search[lang])
        self.search_in_g.setText(texts.search_in_g[lang])
        self.search_in_so.setText(texts.search_in_so[lang])
        self.popup(event.globalPos())


class TextEditWindowMenu(TextEditMenu):
    """TextEditMenu for windows"""

    def __init__(self, parent: QTextEdit | QPlainTextEdit, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)

        self.addSeparator()

        self.exit: QAction = QAction(self)
        self.exit.triggered.connect(lambda: ide.close_window_mode(parent))
        self.exit.setShortcut('Alt+F4')
        self.addAction(self.exit)

    def __call__(self, event: QContextMenuEvent) -> None:
        lang: str = self.lang_s.value('Language')
        self.exit.setText(texts.close_btn[lang])
        super().__call__(event)


class TextEditFullscreenMenu(TextEditWindowMenu):
    """TextEditMenu for presentation mode"""

    def __init__(self, parent: QTextEdit | QPlainTextEdit, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)

        self.addSeparator()

        self.coef: QMenu = QMenu(self)
        self.addMenu(self.coef)
        self.coef_group: QActionGroup = QActionGroup(self.coef)
        self.coef_group.setExclusive(True)
        self.coef_group.triggered.connect(self.coef_triggered)
        for s in ['100%', '125%', '150%', '175%', '200%', '250%', '300%']:
            act: QAction = QAction(s, self)
            act.setCheckable(True)
            if s == '200%':
                act.setChecked(True)
            self.coef_group.addAction(act)
        self.coef.addActions(self.coef_group.actions())

    def __call__(self, event: QContextMenuEvent) -> None:
        lang: str = self.lang_s.value('Language')
        self.coef.setTitle(texts.font_sz_menu[lang])
        super().__call__(event)
        self.exit.setText(texts.exit_presentation_btn[lang])

    def coef_triggered(self, action: QAction) -> None:
        """Reset font size"""
        font: QFont = self.lang_s.value('Font')
        font.setPointSize(int(font.pointSize() * int(action.text()[:-1]) / 100))
        self.p.setFont(font)


class TreeViewMenu(QMenu):
    """Custom QTreeView Menu"""

    def __init__(self, parent: QTreeView, parent_class, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self.p: QTreeView = parent
        self.c: IdeWindow = parent_class

        self.new_btn: QAction = QAction(self)
        self.new_btn.setShortcut(QKeySequence.StandardKey.New)
        self.new_btn.triggered.connect(self.new_file)
        self.addAction(self.new_btn)

        self.copy_btn: QAction = QAction(self)
        self.copy_btn.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_btn.triggered.connect(self.copy_file)
        self.addAction(self.copy_btn)

        self.paste_btn: QAction = QAction(self)
        self.paste_btn.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_btn.triggered.connect(self.paste_file)
        self.addAction(self.paste_btn)

        self.delete_btn: QAction = QAction(self)
        self.delete_btn.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_btn.triggered.connect(self.delete_file)
        self.addAction(self.delete_btn)

        self.rename_btn: QAction = QAction(self)
        self.rename_btn.triggered.connect(self.rename_file)
        self.addAction(self.rename_btn)

        self.open_in_btn: QAction = QAction(self)
        self.open_in_btn.triggered.connect(self.open_in_explorer)
        self.addAction(self.open_in_btn)

        self.lang_s: QSettings = QSettings('Vcode', 'Settings')

    def __call__(self, event: QContextMenuEvent) -> None:
        lang: str = self.lang_s.value('Language')
        self.new_btn.setText(texts.new_btn[lang])
        self.copy_btn.setText(texts.copy[lang])
        self.paste_btn.setText(texts.paste[lang])
        self.delete_btn.setText(texts.delete_btn[lang])
        self.rename_btn.setText(texts.rename_btn[lang])
        self.open_in_btn.setText(texts.open_in_btn[lang])
        self.popup(event.globalPos())

    def new_file(self) -> None:
        """Create a new file"""
        file: InputDialog = InputDialog(texts.new_btn[self.lang_s.value('Language')],
                                        texts.new_btn[self.lang_s.value('Language')], self)
        file.exec()
        if file.text_value():
            if file.text_value().endswith(('/', '\\')):
                mkdir(self.c.model.filePath(self.c.tree.selectedIndexes()[0]) + '/' + file.text_value())
            else:
                x: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0]) + '/' + file.text_value()
                open(x, 'w', encoding=self.lang_s.value('Encoding')).close()
                self.c.add_tab(x)

    def copy_file(self) -> None:
        """Copy file to clipboard"""
        md: QMimeData = QMimeData()
        ls: list[QUrl] = []
        for i in self.c.tree.selectedIndexes():
            ls.append(QUrl('file:///' + self.c.model.filePath(i)))
        md.setUrls(ls)
        app.clipboard().setMimeData(md)

    def paste_file(self) -> None:
        """Paste file from clipboard"""
        new_path: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0])
        if isdir(new_path):
            for url in app.clipboard().mimeData().urls():
                path: str = url.url().replace('file:///', '')
                if isfile(path):
                    shutil.copy2(path, new_path + '/' + app.clipboard().mimeData().urls()[0].fileName())
                elif isdir(path):
                    shutil.copytree(path, new_path + '/' + path.rsplit('/', maxsplit=1)[-1])

    def delete_file(self) -> None:
        """Delete file"""
        n: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0])
        if isfile(n):
            remove(n)
        elif isdir(n):
            shutil.rmtree(n)

    def rename_file(self) -> None:
        """Rename file to new name"""
        file: InputDialog = InputDialog(texts.rename_btn[self.lang_s.value('Language')],
                                        texts.rename_btn[self.lang_s.value('Language')], self)
        path, name = self.c.model.filePath(self.c.tree.selectedIndexes()[0]).rsplit('/', maxsplit=1)
        file.le.setText(name)
        file.exec()
        if file.text_value() != name:
            try:
                rename(path + '/' + name, path + '/' + file.text_value())
            except Exception:
                pass

    def open_in_explorer(self) -> None:
        """Open file or directory in explorer"""
        pth: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0]).replace('/', '\\')
        if isfile(pth):
            pth = pth.rsplit('\\', maxsplit=1)[0]
        if sys.platform == 'win32':
            system(f'explorer "{pth}"')
        elif sys.platform.startswith('linux'):
            system(f'xdg-open "{pth}"')


class LineEditMenu(QMenu):
    """Custom QLineEdit QMenu"""

    def __init__(self, parent: QLineEdit, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self.p: QLineEdit = parent

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

        self.lang_s: QSettings = QSettings('Vcode', 'Settings')

    def __call__(self, event: QContextMenuEvent) -> None:
        lang: str = self.lang_s.value('language')
        self.undo.setText(texts.undo[lang])
        self.redo.setText(texts.redo[lang])
        self.cut.setText(texts.cut[lang])
        self.copy.setText(texts.copy[lang])
        self.paste.setText(texts.paste[lang])
        self.select_all.setText(texts.select_all[lang])
        self.popup(event.globalPos())


class TabBarMenu(QMenu):
    """Menu for tab bar"""

    def __init__(self, parent: QTabWidget, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self.p: QTabWidget = parent
        self.selected_pos: QPoint | None = None

        self.close_current: QAction = QAction(self)
        self.close_current.triggered.connect(self.close_cur_tab)
        self.addAction(self.close_current)

        self.close_all: QAction = QAction(self)
        self.close_all.triggered.connect(self.close_all_tabs)
        self.addAction(self.close_all)

        self.addSeparator()

        self.new_window: QAction = QAction(self)
        self.new_window.triggered.connect(lambda: ide.new_window(self.p.tabBar().tabAt(self.selected_pos)))
        self.addAction(self.new_window)

        self.addSeparator()

        self.open_in: QAction = QAction(self)
        self.open_in.triggered.connect(self.open_in_explorer)
        self.addAction(self.open_in)

        self.addSeparator()

        self.start: QAction = QAction(self)
        self.start.triggered.connect(self.start_pr)
        self.addAction(self.start)

        self.debug: QAction = QAction(self)
        self.debug.triggered.connect(self.debug_pr)
        self.addAction(self.debug)

        self.lang_s: QSettings = QSettings('Vcode', 'Settings')

    def __call__(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.RightButton or self.childAt(event.pos()) is not None or not self.p.count():
            return
        lang: str = self.lang_s.value('Language')
        self.close_current.setText(texts.close_btn[lang])
        self.close_all.setText(texts.close_all_btn[lang])
        self.new_window.setText(texts.new_window_btn[lang])
        self.open_in.setText(texts.open_in_btn[lang])
        self.start.setText(texts.start_btn[lang])
        self.debug.setText(texts.debug_btn[lang])
        self.popup(event.globalPosition().toPoint())
        self.selected_pos = event.pos()

    def close_tab(self, index: int) -> None:
        """Close tab"""
        widget: EditorTab = self.p.widget(index)
        if widget.saved_text != widget.toPlainText():
            button_text: str = WarningMessageBox(self, 'Warning', texts.save_warning, WarningMessageBox.SAVE).wait()
            if button_text in texts.cancel_btn.values():
                return
            elif button_text in texts.save_btn.values():
                widget.save()
        widget.deleteLater()

    def close_cur_tab(self) -> None:
        """Close selected or current tab"""
        if (x := self.p.tabBar().tabAt(self.selected_pos)) != -1:
            self.close_tab(x)
            self.p.removeTab(x)
        else:
            self.close_tab(self.p.currentIndex())
            self.p.removeTab(self.p.currentIndex())

    def close_all_tabs(self) -> None:
        """Close all tabs"""
        for tab in range(self.p.count()):
            self.close_tab(0)
            self.p.removeTab(0)

    def open_in_explorer(self) -> None:
        """Open file or directory in explorer"""
        if (x := self.p.tabBar().tabAt(self.selected_pos)) != -1 and type(self.p.widget(x)):
            pth: str = self.p.widget(x).path
        elif type(self.p.currentWidget()) in (EditorTab, GitTab):
            pth: str = self.p.currentWidget().path
        else:
            return
        if sys.platform == 'win32':
            system(f'start "" "{pth}"')
        elif sys.platform.startswith('linux'):
            system(f'xdg-open "{pth}"')

    def start_pr(self) -> None:
        """Start program in tab"""
        if (x := self.p.tabBar().tabAt(self.selected_pos)) != -1:
            ide.start_program(self.p.widget(x))
        else:
            ide.start_program(self.p.currentWidget())

    def debug_pr(self) -> None:
        """Debug program in tab"""
        if (x := self.p.tabBar().tabAt(self.selected_pos)) != -1:
            ide.debug_program(self.p.widget(x))
        else:
            ide.debug_program(self.p.currentWidget())


class SystemMonitor(QDialog):
    """Show CPU percent and memory usage"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Vcode System monitor')
        self.setMinimumSize(300, 200)
        self.lay: QVBoxLayout = QVBoxLayout(self)
        self.setLayout(self.lay)

        self.ide_process: psutil.Process = psutil.Process(getpid())
        self.list_processes: list[psutil.Process] = []

        self.processor: QProgressBar = QProgressBar(self)
        self.processor.setObjectName('monitor')
        self.processor.setFormat('CPU usage: %p%')
        self.lay.addWidget(self.processor)

        self.ram: QProgressBar = QProgressBar(self)
        self.ram.setObjectName('monitor')
        self.ram.setFormat('Memory usage: %p% - %v MB')
        self.ram.setMaximum(self.bytes_to_mb(psutil.virtual_memory().total))
        self.lay.addWidget(self.ram)

        self.ide: QProgressBar = QProgressBar(self)
        self.ide.setObjectName('monitor')
        self.ide.setFormat('Vcode memory usage: %p% - %v MB')
        self.ide.setMaximum(self.bytes_to_mb(psutil.virtual_memory().total))
        self.lay.addWidget(self.ide)

        self.monitor()

        self.timer: QTimer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.monitor)
        self.timer.start()

    def monitor(self) -> None:
        """Update values"""
        self.processor.setValue(int(psutil.cpu_percent()))
        self.ram.setValue(self.bytes_to_mb(psutil.virtual_memory().used))
        self.ide.setValue(self.bytes_to_mb(self.ide_process.memory_info().rss))

    @staticmethod
    def bytes_to_mb(a: int | float) -> int:
        """Convert bytes to megabytes"""
        return int(a / 1024 / 1024)

    def closeEvent(self, a0: QCloseEvent) -> None:
        """Stop updating monitor"""
        self.timer.stop()


class GitTab(QWidget):
    """Tab with git repository"""

    def __init__(self, path: str, parent_exit_code_label: QLabel | None = None, parent=None) -> None:
        if parent_exit_code_label is not None:
            self.exit_code: QLabel = parent_exit_code_label
        else:
            self.exit_code: QLabel = QLabel()
        if not GIT_INSTALLED:
            self.exit_code.setText('Git not installed')
            return
        super().__init__(parent=parent)
        self.p: IdeWindow = parent
        self.path: str = path
        self.l_s: QSettings = QSettings('Vcode', 'Settings')

        self.git_repo: git.Repo = git.Repo(path)

        self.lay: QGridLayout = QGridLayout(self)
        self.bar: QToolBar = QToolBar(self)
        self.lay.addWidget(self.bar)

        self.commit: QAction = QAction('Commit', self)
        self.commit.triggered.connect(self.git_commit)
        self.bar.addAction(self.commit)

        self.push: QAction = QAction('Push', self)
        self.push.triggered.connect(self.git_push)
        self.bar.addAction(self.push)

        self.merge: QAction = QAction('Merge', self)
        self.merge.triggered.connect(self.git_merge)
        self.bar.addAction(self.merge)

        self.branch: QComboBox = QComboBox(self)
        self.branch.addItems([i.name for i in self.git_repo.branches])
        self.branch.setCurrentText(self.git_repo.active_branch.name)
        self.branch.currentTextChanged.connect(lambda: self.change_branch(self.branch.currentText()))
        self.lay.addWidget(self.branch)

        self.repo_list: QTreeView = QTreeView(self)
        self.repo_list_model: QFileSystemModel = QFileSystemModel(self)
        self.repo_list_model.setRootPath(path)
        self.repo_list.setModel(self.repo_list_model)
        self.repo_list.setRootIndex(self.repo_list_model.index(path))
        self.repo_list.doubleClicked.connect(lambda x: self.p.add_tab(self.repo_list_model.filePath(x)))
        self.lay.addWidget(self.repo_list)

    def change_branch(self, branch: str) -> None:
        """Change current branch"""
        self.git_repo.head.reference = branch
        self.git_repo.head.reset(working_tree=True)

    def git_merge(self) -> None:
        """Merge from other commits"""
        self.git_repo.merge_base()

    def git_commit(self) -> None:
        """Create new commit"""
        git_descr: InputDialog = InputDialog(texts.rename_btn[self.l_s.value('Language')],
                                             texts.rename_btn[self.l_s.value('Language')], self)
        git_descr.exec()
        if git_descr.text_value():
            for i in self.repo_list.selectedIndexes():
                self.git_repo.index.add(self.repo_list_model.filePath(i))
            self.git_repo.index.commit(git_descr.text_value())

    def git_push(self) -> None:
        """Push commits"""
        self.git_repo.remotes.origin.push()


class EditorTab(QPlainTextEdit):
    """Editor text place"""

    def __init__(self, file: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.line_num: LineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width()

        self.pr_settings: QSettings = QSettings('Vcode', 'Settings')
        self.file: str = file.replace('\\', '/')
        self.path, self.filename = self.file.rsplit('/', maxsplit=1)
        try:
            with open(file, encoding=self.pr_settings.value('Encoding')) as cf:
                self.setPlainText(cf.read())
        except UnicodeDecodeError:
            self.setPlainText(texts.unsupported_encoding[self.pr_settings.value('Language')])
            self.te: QPushButton = QPushButton(texts.open_uns_btn[self.pr_settings.value('Language')], self)
            self.te.setGeometry(50, self.font().pointSize() + 20, 200, 30)
            self.te.clicked.connect(lambda: startfile(self.file))
            self.setReadOnly(True)
            self.save = lambda: None
            self.line_num.setVisible(False)
        self.saved_text: str = self.toPlainText()
        self.highlighter: Highlighter | None = None
        self.completer: QCompleter | None = None
        self.start_command: str | None = None
        self.debug_command: str | None = None
        self.language: str = ''

    def set_highlighter(self, highlighter: Highlighter) -> None:
        """Add highlighter to code"""
        self.highlighter: Highlighter = highlighter
        self.highlighter.setDocument(self.document())
        if self.highlighter.complete_words:
            self.completer = QCompleter(self.highlighter.complete_words, self)
            self.completer.setWidget(self)
            self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.completer.activated.connect(self.insert_completion)

    def save(self) -> None:
        """Save text to file"""
        with open(self.file, 'w', encoding=self.pr_settings.value('Encoding')) as sf:
            sf.write(self.toPlainText())
        self.saved_text: str = self.toPlainText()

    def line_number_area_width(self) -> int:
        """Return sizes of text area"""
        return max(45, 5 + self.fontMetrics().boundingRect('9').width() * (len(str(self.blockCount())) + 3))

    def update_line_number_area_width(self) -> None:
        """Set sizes of text area"""
        self.setViewportMargins(self.line_number_area_width() + 7, 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        """Update sizes of text area"""
        if dy:
            self.line_num.scroll(0, dy)
        else:
            self.line_num.update(0, rect.y(), self.line_num.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Resize event"""
        super().resizeEvent(event)
        cr: QRect = self.contentsRect()
        self.line_num.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def update_line_event(self, event: QPaintEvent) -> None:
        """Update line number area"""
        painter: QPainter = QPainter(self.line_num)
        painter.setFont(self.font())
        block: QTextBlock = self.firstVisibleBlock()
        block_number: int = block.blockNumber()
        top: float = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom: float = top + self.blockBoundingRect(block).height()
        height: int = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                painter.drawText(QRect(0, int(top), self.line_num.width(), height),
                                 Qt.AlignmentFlag.AlignRight, str(block_number + 1) + ' |')
            block: QTextBlock = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self) -> None:
        """Highlight selected line"""
        selections: list = []
        if not self.isReadOnly():
            selection: QTextEdit.ExtraSelection = QTextEdit.ExtraSelection()
            color: QColor = self.palette().color(QPalette.ColorRole.Window).toRgb()
            selection.format.setBackground(QColor(color.red() - 10, color.green() - 10, color.blue() - 10))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor: QTextCursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)
        self.setExtraSelections(selections)

    def cursor_word(self, sentence: str) -> str:
        """Cursor word"""
        p: int = sentence.replace('\n', ' ').rfind(' ')
        if p == -1:
            return sentence
        return sentence[p + 1:]

    def insert_completion(self, text: str) -> None:
        """Insert completion to text"""
        p: int = self.toPlainText().replace('\n', ' ').rfind(' ')
        cursor: QTextCursor = self.textCursor()
        if p == -1:
            self.setPlainText(text)
        else:
            self.setPlainText(self.toPlainText()[:p + 1] + text)
        self.setTextCursor(cursor)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        """Reaction on key pressed"""
        txt_: str = self.toPlainText()
        cursor: QTextCursor = self.textCursor()
        tab_sz: int = self.pr_settings.value('Tab size')
        if e.key() == Qt.Key.Key_Tab:
            cursor.insertText(' ' * tab_sz + f'\n{" " * tab_sz}'.join(
                cursor.selection().toPlainText().split('\n')))
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_Return:
            txt_1: str = txt_[:cursor.position()].rsplit('\n', maxsplit=1)[-1]
            cursor.insertText('\n' + re.split(r'\S', txt_1, 1)[0])
            if cursor.position() <= len(txt_) and txt_1:
                if txt_1[-1] == '(' and txt_[cursor.position() - 1] == ')' or \
                        txt_1[-1] == '[' and txt_[cursor.position() - 1] == ']' or \
                        txt_1[-1] == '{' and txt_[cursor.position() - 1] == '}' or \
                        txt_1[-1] == '<' and txt_[cursor.position() - 1] == '>':
                    cursor.insertText(' ' * tab_sz + '\n')
                elif '(' in txt_1 and txt_[cursor.position() - 1] == ')':
                    cursor.insertText(' ' * len(txt_1.split('(')[0]) + ' ')
                elif '[' in txt_1 and txt_[cursor.position() - 1] == ']':
                    if tt := re.search(r'\S', txt_1):
                        cursor.insertText(' ' * tt.start())
                elif '{' in txt_1 and txt_[cursor.position() - 1] == '}':
                    cursor.insertText(' ' * len(txt_1.split('[')[0]) + ' ')
                elif '<' in txt_1 and txt_[cursor.position() - 1] == '>':
                    if tt := re.search(r'\S', txt_1):
                        cursor.insertText(' ' * tt.start())
            if (fa := re.findall(r'\b\S+\b', txt_1)) and fa[0] in self.highlighter.tab_words:
                cursor.insertText(' ' * tab_sz)
            self.setTextCursor(cursor)
            e.accept()
        elif (e.key() == Qt.Key.Key_Backspace and cursor.position() < len(txt_) and
              txt_[cursor.position() - 1] + txt_[cursor.position()] in ['()', '[]', '{}', '<>', '\'\'', '""']):
            cursor.setPosition(cursor.position() + 1)
            cursor.setPosition(cursor.position() - 2, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
            e.accept()
        elif (e.key() == Qt.Key.Key_Backspace and not cursor.selectedText() and
              txt_[cursor.position() - tab_sz:cursor.position()] == ' ' * tab_sz):
            cursor.setPosition(cursor.position() - tab_sz, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_ParenLeft:
            cursor.insertText(f'({cursor.selection().toPlainText()})')
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_BracketLeft:
            cursor.insertText(f'[{cursor.selection().toPlainText()}]')
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_BraceLeft:
            cursor.insertText(f'{{{cursor.selection().toPlainText()}}}')
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_Less and cursor.selectedText():
            cursor.insertText(f'<{cursor.selection().toPlainText()}>')
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_Apostrophe and (cursor.selectedText() or
                                                   cursor.position() == len(txt_) or
                                                   txt_[cursor.position()] in ' \n'):
            cursor.insertText(f'\'{cursor.selection().toPlainText()}\'')
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_QuoteDbl and (cursor.selectedText() or
                                                 cursor.position() == len(txt_) or
                                                 txt_[cursor.position()] in ' \n'):
            cursor.insertText(f'"{cursor.selection().toPlainText()}"')
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_ParenRight and (cursor.position() < len(txt_) and
                                                   txt_[cursor.position() - 1] == '(' and
                                                   txt_[cursor.position()] == ')'):
            cursor.movePosition(QTextCursor.MoveOperation.Right)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_BracketRight and (cursor.position() < len(txt_) and
                                                     txt_[cursor.position() - 1] == '[' and
                                                     txt_[cursor.position()] == ']'):
            cursor.movePosition(QTextCursor.MoveOperation.Right)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_BraceRight and (cursor.position() < len(txt_) and
                                                   txt_[cursor.position() - 1] == '{' and
                                                   txt_[cursor.position()] == '}'):
            cursor.movePosition(QTextCursor.MoveOperation.Right)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_Apostrophe and (
                cursor.position() < len(txt_) and
                txt_[cursor.position() - 1] == txt_[cursor.position()] == '\''):
            cursor.movePosition(QTextCursor.MoveOperation.Right)
            self.setTextCursor(cursor)
            e.accept()
        elif e.key() == Qt.Key.Key_QuoteDbl and (
                cursor.position() < len(txt_) and
                txt_[cursor.position() - 1] == txt_[cursor.position()] == '"'):
            cursor.movePosition(QTextCursor.MoveOperation.Right)
            self.setTextCursor(cursor)
            e.accept()
        else:
            QPlainTextEdit.keyPressEvent(self, e)

        if not self.completer or not self.toPlainText():
            return
        self.completer.setCompletionPrefix(self.cursor_word(self.toPlainText()))
        if len(self.completer.completionPrefix()) < 1:
            self.completer.popup().hide()
            return
        self.completer.complete()

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        pass

    def dropEvent(self, e: QDropEvent) -> None:
        mime: QMimeData = e.mimeData()
        if mime.hasUrls():
            self.parent().dropEvent(e)
        elif mime.hasText():
            super().dropEvent(e)
        else:
            e.ignore()


class LineNumberArea(QWidget):
    """Area for numbers of lines"""

    def __init__(self, editor: EditorTab) -> None:
        super().__init__(editor)
        self.editor: EditorTab = editor

    def paintEvent(self, event: QPaintEvent) -> None:
        self.editor.update_line_event(event)


class TabWidget(QTabWidget):
    """Custom QTabWidget"""

    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.lalay: QHBoxLayout = QHBoxLayout()
        self.empty_widget: QPushButton = QPushButton(self)
        self.lalay.addWidget(self.empty_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.lalay)
        self.currentChanged.connect(self.empty)

        self.mouseReleaseEvent = TabBarMenu(self)

    def empty(self) -> None:
        """Show button when tab list is empty"""
        if not self.count():
            self.empty_widget.setVisible(True)
        else:
            self.empty_widget.setVisible(False)


class FindWindow(QDialog):
    """Find all text usages of string"""

    def __init__(self, parent: EditorTab | None = None) -> None:
        super().__init__(parent)
        self.parent: EditorTab = parent
        self.setModal(True)
        self.setMinimumSize(400, 150)
        layout: QVBoxLayout = QVBoxLayout(self)
        self.setLayout(layout)
        self.setWindowTitle(texts.find_btn[self.parent.pr_settings.value('Language')])

        self.find_line: QLineEdit = QLineEdit(self)
        self.find_line.textChanged.connect(self.search)
        self.find_line.contextMenuEvent = LineEditMenu(self.find_line)
        layout.addWidget(self.find_line)

        self.list: QListWidget = QListWidget(self)
        self.list.itemClicked.connect(self.go_to_line)
        layout.addWidget(self.list)

        self.counter: QLabel = QLabel('Total results: 0', self)
        layout.addWidget(self.counter)

    def search(self) -> None:
        """Scat text for search usages"""
        self.list.clear()
        find: str = self.find_line.text()
        if find:
            text: list[str] = self.parent.toPlainText().split('\n')
            for i in range(self.parent.blockCount()):
                if find in text[i].lower():
                    self.list.addItem(f'Line {i}: "{text[i]}"')
        self.counter.setText(f'Total results: {self.list.count()}')

    def go_to_line(self, key: QListWidgetItem) -> None:
        """Open selected line in text"""
        self.parent.setTextCursor(
            QTextCursor(self.parent.document().findBlockByLineNumber(int(key.text()[5:].split(':')[0]))))


class HighlightMakerString(QWidget):
    """Editor string for highlight maker"""

    def __init__(self, rstring: str, params: str) -> None:
        super().__init__()
        layout: QHBoxLayout = QHBoxLayout()
        self.setLayout(layout)

        self.rstring: QLineEdit = QLineEdit(rstring, self)
        self.rstring.contextMenuEvent = LineEditMenu(self.rstring)
        layout.addWidget(self.rstring)

        self.json_params: QLineEdit = QLineEdit(params[1:-1], self)
        self.json_params.contextMenuEvent = LineEditMenu(self.json_params)
        layout.addWidget(self.json_params)

        self.remove_btn: QPushButton = QPushButton('-', self)
        layout.addWidget(self.remove_btn)


class IdeWindow(QMainWindow):
    """Main app window"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Vcode')
        self.setMinimumSize(300, 100)
        self.setAcceptDrops(True)

        self.settings: QSettings = QSettings('Vcode', 'Settings')
        self.options: QSettings = QSettings('Vcode', 'Options')
        self.history: QSettings = QSettings('Vcode', 'History')

        self.settings_window: SettingsDialog = SettingsDialog(self)
        if 'System' in style.keys():
            st_rb: QRadioButton = QRadioButton('System', self)
            if 'System' == self.settings.value('Style'):
                st_rb.setChecked(True)
            st_rb.clicked.connect(lambda: self.select_style('System'))
            self.settings_window.style_select_layout.addWidget(st_rb)
        for st in style.keys():
            if st != 'System':
                st_rb: QRadioButton = QRadioButton(st, self)
                if st == self.settings.value('Style'):
                    st_rb.setChecked(True)
                st_rb.clicked.connect(lambda: self.select_style(self.sender().text()))
                self.settings_window.style_select_layout.addWidget(st_rb)

        self.editor_tabs: TabWidget = TabWidget(self)
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        self.editor_tabs.currentChanged.connect(self.sel_tab)
        self.editor_tabs.empty_widget.clicked.connect(self.open_file)

        self.model: QFileSystemModel = QFileSystemModel(self)
        self.model.setRootPath('')
        self.model.setFilter(QDir.Filter.Hidden | QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Files)
        self.tree: QTreeView = QTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.doubleClicked.connect(lambda x: self.add_tab(self.model.filePath(x)))
        self.tree.contextMenuEvent = TreeViewMenu(self.tree, self)

        self.splitter: QSplitter = QSplitter()
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.editor_tabs)
        self.setCentralWidget(self.splitter)

        self.tool_bar: QToolBar = QToolBar(self)
        self.tool_bar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.tool_bar)

        self.start_btn: QAction = QAction(self)
        self.start_btn.setShortcut('F5')
        self.start_btn.triggered.connect(self.start_program)
        self.tool_bar.addAction(self.start_btn)

        self.debug_btn: QAction = QAction(self)
        self.debug_btn.setShortcut('Shift+F5')
        self.debug_btn.triggered.connect(self.debug_program)
        self.tool_bar.addAction(self.debug_btn)

        self.tool_bar.addSeparator()
        self.exit_code: QLabel = QLabel('-')
        self.exit_code.setObjectName('exit_code')
        self.tool_bar.addWidget(self.exit_code)

        empty: QWidget = QWidget()
        empty.setObjectName('empty')
        empty.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tool_bar.addWidget(empty)

        self.position_code: QLabel = QLabel('0:0')
        self.position_code.setObjectName('exit_code')
        self.tool_bar.addWidget(self.position_code)

        self.selection_code: QLabel = QLabel('()')
        self.selection_code.setObjectName('exit_code')
        self.tool_bar.addWidget(self.selection_code)

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

        self.file_menu.addSeparator()

        self.history_btn: QMenu = QMenu(self)
        self.history_btn.setToolTipsVisible(True)
        self.file_menu.addMenu(self.history_btn)

        self.delete_history_btn: QAction = QAction(self)
        self.delete_history_btn.triggered.connect(self.delete_history)
        self.update_history_menu()

        self.file_menu.addSeparator()

        self.save_btn: QAction = QAction(self)
        self.save_btn.setShortcut(QKeySequence.StandardKey.Save)
        self.save_btn.triggered.connect(self.save_file)
        self.file_menu.addAction(self.save_btn)

        self.save_as_btn: QAction = QAction(self)
        self.save_as_btn.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_btn.triggered.connect(self.save_as)
        self.file_menu.addAction(self.save_as_btn)

        self.file_menu.addSeparator()

        self.exit_btn: QAction = QAction(self)
        self.exit_btn.setShortcut('Alt+F4')
        self.exit_btn.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_btn)

        self.edit_menu: QMenu = QMenu(self)
        self.edit_menu.setEnabled(False)
        self.menuBar().addMenu(self.edit_menu)

        self.undo: QAction = QAction(self)
        self.undo.triggered.connect(lambda: self.editor_tabs.currentWidget().undo())
        self.undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.edit_menu.addAction(self.undo)

        self.redo: QAction = QAction(self)
        self.redo.triggered.connect(lambda: self.editor_tabs.currentWidget().redo())
        self.redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.edit_menu.addAction(self.redo)

        self.edit_menu.addSeparator()

        self.cut: QAction = QAction(self)
        self.cut.triggered.connect(lambda: self.editor_tabs.currentWidget().cut())
        self.cut.setShortcut(QKeySequence.StandardKey.Cut)
        self.edit_menu.addAction(self.cut)

        self.copy: QAction = QAction(self)
        self.copy.triggered.connect(lambda: self.editor_tabs.currentWidget().copy())
        self.copy.setShortcut(QKeySequence.StandardKey.Copy)
        self.edit_menu.addAction(self.copy)

        self.paste: QAction = QAction(self)
        self.paste.triggered.connect(lambda: self.editor_tabs.currentWidget().paste())
        self.paste.setShortcut(QKeySequence.StandardKey.Paste)
        self.edit_menu.addAction(self.paste)

        self.select_all: QAction = QAction(self)
        self.select_all.triggered.connect(lambda: self.editor_tabs.currentWidget().selectAll())
        self.select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.edit_menu.addAction(self.select_all)

        self.edit_menu.addSeparator()

        self.find_btn: QAction = QAction(self)
        self.find_btn.triggered.connect(lambda: FindWindow(self.editor_tabs.currentWidget()).exec())
        self.find_btn.setShortcut(QKeySequence.StandardKey.Find)
        self.edit_menu.addAction(self.find_btn)

        self.view_menu: QMenu = QMenu(self)
        self.menuBar().addMenu(self.view_menu)

        self.terminal_btn: QAction = QAction(self)
        self.terminal_btn.setShortcut('Ctrl+T')
        self.terminal_btn.triggered.connect(self.start_terminal)
        self.view_menu.addAction(self.terminal_btn)

        self.monitor_btn: QAction = QAction(self)
        self.monitor_btn.triggered.connect(self.show_monitor)
        self.view_menu.addAction(self.monitor_btn)

        self.presentation_btn: QAction = QAction(self)
        self.presentation_btn.setShortcuts(['Ctrl+F11', 'F11'])
        self.presentation_btn.triggered.connect(self.presentation_mode)
        self.view_menu.addAction(self.presentation_btn)

        self.settings_btn: QAction = QAction(self)
        self.settings_btn.triggered.connect(self.settings_window.exec)
        self.menuBar().addAction(self.settings_btn)

        self.git_menu: QMenu = QMenu('Git', self)
        self.menuBar().addMenu(self.git_menu)

        self.git_open_btn: QAction = QAction('Open', self)
        self.git_open_btn.triggered.connect(self.git_open)
        self.git_menu.addAction(self.git_open_btn)

        self.git_init_btn: QAction = QAction('Init', self)
        self.git_init_btn.triggered.connect(self.git_init)
        self.git_menu.addAction(self.git_init_btn)

        self.git_clone_btn: QAction = QAction('Clone', self)
        self.git_clone_btn.triggered.connect(self.git_clone)
        self.git_menu.addAction(self.git_clone_btn)

        self.about_menu: QMenu = QMenu(self)
        self.menuBar().addMenu(self.about_menu)

        self.about_btn: QAction = QAction(self)
        self.about_btn.triggered.connect(AboutDialog(self).exec)
        self.about_menu.addAction(self.about_btn)

        self.feedback_btn: QAction = QAction(self)
        self.feedback_btn.triggered.connect(lambda: openweb('https://vcodeide.ru/feedback/'))
        self.about_menu.addAction(self.feedback_btn)

        self.about_menu.addSeparator()

        self.check_updates_btn: QAction = QAction(self)
        self.check_updates_btn.triggered.connect(self.check_updates)
        self.about_menu.addAction(self.check_updates_btn)

        self.download_btn: QAction = QAction(self)
        self.download_btn.triggered.connect(lambda: openweb('https://vcodeide.ru/download/'))

        if len(self.settings.allKeys()) == 8:
            self.select_language(self.settings.value('Language'))
            self.select_style(self.settings.value('Style'))
        else:
            if self.settings.value('Autorun') is None:
                self.settings.setValue('Autorun', 0)
            if self.settings.value('Autosave') is None:
                self.settings.setValue('Autosave', 0)
            if self.settings.value('Recent') is None:
                self.settings.setValue('Recent', 1)
            if self.settings.value('Font') is None:
                if 'Consolas' in QFontDatabase.families():
                    self.settings.setValue('Font', QFont('Consolas', 12))
                else:
                    self.settings.setValue('Font', QFont())
            if self.settings.value('Language') is None:
                self.select_language('en')
            if self.settings.value('Style') is None:
                self.select_style('System')
            if self.settings.value('Encoding') is None:
                self.settings.setValue('Encoding', 'utf-8')
                next(filter(lambda x: x.text() == 'System',
                            self.settings_window.findChildren(QRadioButton))).setChecked(True)
            if self.settings.value('Tab size') is None:
                self.settings.setValue('Tab size', 4)

        if not self.options.allKeys():
            self.options.setValue('Splitter', [225, 775])
            self.options.setValue('Folder', USER)
            self.options.setValue('Geometry', 'Not init')
        self.splitter.setSizes(map(int, self.options.value('Splitter')))

        self.settings_window.language.setCurrentText(self.settings.value('Language').upper())
        self.settings_window.language.currentTextChanged.connect(
            lambda: self.select_language(self.settings_window.language.currentText().lower()))

        self.settings_window.encoding.setCurrentText(self.settings.value('Encoding'))
        self.settings_window.encoding.currentTextChanged.connect(
            lambda: self.settings.setValue('Encoding', self.settings_window.encoding.currentText()))

        self.settings_window.autorun.setChecked(bool(self.settings.value('Autorun')))
        self.settings_window.autorun.stateChanged.connect(self.autorun_check)

        self.settings_window.autosave.setChecked(bool(self.settings.value('Autosave')))
        self.settings_window.autosave.stateChanged.connect(
            lambda: self.settings.setValue('Autosave', int(self.settings_window.autosave.isChecked())))

        self.settings_window.recent.setChecked(bool(self.settings.value('Recent')))
        self.settings_window.recent.stateChanged.connect(
            lambda: self.settings.setValue('Recent', int(self.settings_window.recent.isChecked())))

        self.settings_window.tab_size.setValue(int(self.settings.value('Tab size')))
        self.settings_window.tab_size.valueChanged.connect(
            lambda: self.settings.setValue('Tab size', self.settings_window.tab_size.value()))

        self.settings_window.fonts.setCurrentText(self.settings.value('Font').family())
        self.settings_window.fonts.currentTextChanged.connect(self.select_font)

        self.settings_window.font_size.setValue(self.settings.value('Font').pointSize())
        self.settings_window.font_size.valueChanged.connect(self.select_font)

        self.show_ide()
        self.check_updates(show_else=False)

        self.position_code.setText('')
        self.selection_code.setText('')

    def show_ide(self) -> None:
        """Show main ide window"""
        if self.options.value('Geometry') == 'Maximized':
            self.showMaximized()
        elif self.options.value('Geometry') == 'Not init':
            self.resize(1000, 700)
            self.show()
        else:
            self.setGeometry(self.options.value('Geometry'))
            self.show()

    def check_updates(self, *, show_else: bool = True) -> None:
        """Checking for updates"""

        def check() -> None:
            try:
                if list(map(int, VERSION.split('.'))) < list(
                        map(int, get('https://version.vcodeide.ru/', verify=False).text.split('.'))):
                    self.menuBar().addAction(self.download_btn)
                    act_true.trigger()
                elif show_else:
                    act_false.trigger()
            except OSError:
                pass

        def show_update_message() -> None:
            msg: str = WarningMessageBox(self, 'Vcode Updater', texts.update_warning, WarningMessageBox.UPDATE).wait()
            if msg == texts.update_btn[self.settings.value('Language')]:
                self.download_btn.trigger()

        def show_else_message() -> None:
            WarningMessageBox(self, 'Vcode Updater', texts.update_not).wait()

        act_true: QAction = QAction()
        act_true.triggered.connect(show_update_message)
        act_false: QAction = QAction()
        act_false.triggered.connect(show_else_message)
        threading.Thread(target=check).start()

    def show_monitor(self) -> None:
        """Run system monitor"""
        SystemMonitor(self).show()

    def sel_tab(self) -> None:
        """Change current tab"""
        if self.editor_tabs.count():
            self.setWindowTitle(self.editor_tabs.currentWidget().windowTitle() + ' - Vcode')
            if type(self.editor_tabs.currentWidget()) == EditorTab:
                d: list[str] = self.editor_tabs.currentWidget().file.split('/')
                for _ in range(len(d)):
                    self.tree.setExpanded(self.model.index('/'.join(d)), True)
                    del d[-1]
                self.tree.selectionModel().select(self.model.index(self.editor_tabs.currentWidget().file),
                                                  QItemSelectionModel.SelectionFlag.Select)
                self.position_code.setText('0:0')
                self.selection_code.setText('')
                self.edit_menu.setEnabled(True)
            else:
                self.tree.selectionModel().select(self.model.index(self.editor_tabs.currentWidget().path),
                                                  QItemSelectionModel.SelectionFlag.Select)
                self.position_code.setText('')
                self.selection_code.setText('')
                self.edit_menu.setEnabled(False)
        else:
            self.setWindowTitle('Vcode')
            self.position_code.setText('')
            self.selection_code.setText('')
            self.edit_menu.setEnabled(False)

    def add_tab(self, filename: str, row: int | None = None) -> None:
        """Add new text tab"""
        if not isfile(filename):
            return
        for tab in self.editor_tabs.findChildren(EditorTab):
            if tab.file == filename:
                self.editor_tabs.setCurrentWidget(tab)
                return
        filename = filename.replace('\\', '/')
        if filename.endswith('.hl'):
            hmt: HighlightMaker = HighlightMaker(filename)
            hmt.setWindowTitle(f'{filename.split("/")[-1]} - Vcode highlight maker')
            hmt.exec()
            return
        editor: EditorTab = EditorTab(filename, self)
        editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        editor.textChanged.connect(self.auto_save)
        editor.setFont(self.settings.value('Font'))
        editor.contextMenuEvent = TextEditMenu(editor)
        editor.cursorPositionChanged.connect(lambda: self.position_code.setText('{}:{}'.format(
            editor.textCursor().blockNumber() + 1, editor.textCursor().positionInBlock() + 1)))
        editor.selectionChanged.connect(lambda: self.selection_code.setText(
            f' ({se} chars)' if (se := editor.textCursor().selectionEnd() - editor.textCursor().selectionStart()) > 1
            else ''))
        c: QTextCursor = editor.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)
        editor.setTextCursor(c)
        editor.setFocus()
        editor.cursorPositionChanged.connect(editor.highlight_current_line)
        for langname, language in language_list.items():
            if filename.rsplit('.', maxsplit=1)[-1] in language['file_formats']:
                editor.set_highlighter(Highlighter(resource_path(language['highlight'])))
                editor.start_command = language['start_command']
                editor.debug_command = language['debug_command']
                editor.language = langname
        editor.setWindowTitle(editor.filename)
        for item in self.history.allKeys():
            if self.history.value(item) == filename:
                self.history.remove(item)
        self.history.setValue(str(len(self.history.allKeys())), filename)
        self.update_history()
        self.update_history_menu()
        if row is None:
            self.editor_tabs.setCurrentIndex(self.editor_tabs.addTab(editor, editor.filename))
        else:
            self.editor_tabs.setCurrentIndex(self.editor_tabs.insertTab(row, editor, editor.filename))
        self.editor_tabs.setTabToolTip(self.editor_tabs.currentIndex(), editor.file)

    def add_git_tab(self, path: str, row: int | None = None) -> None:
        """Add new git repository tab"""
        if not isdir(path):
            return
        editor: GitTab = GitTab(path, self.exit_code, self)
        editor.setWindowTitle('Git: ' + editor.path.rsplit('/', maxsplit=1)[-1])
        if row is None:
            self.editor_tabs.setCurrentIndex(self.editor_tabs.addTab(editor, path.split('/')[-1]))
        else:
            self.editor_tabs.setCurrentIndex(self.editor_tabs.insertTab(row, editor, path.split('/')[-1]))
        self.editor_tabs.setTabToolTip(self.editor_tabs.currentIndex(), path)

    def close_tab(self, tab: int) -> None:
        """Close tab"""
        widget: EditorTab | GitTab = self.editor_tabs.widget(tab)
        if type(widget) is EditorTab:
            if widget.saved_text != widget.toPlainText():
                button_text: str = WarningMessageBox(self, 'Warning', texts.save_warning, WarningMessageBox.SAVE).wait()
                if button_text in texts.cancel_btn.values():
                    return
                elif button_text in texts.save_btn.values():
                    widget.save()
        widget.deleteLater()
        self.editor_tabs.removeTab(tab)

    def new_window(self, tab: int) -> None:
        """Show current tab in new window"""
        t: EditorTab | GitTab | QWidget = self.editor_tabs.widget(tab)
        if type(t) is EditorTab:
            self.editor_tabs.removeTab(tab)
            t.contextMenuEvent = TextEditWindowMenu(t)
            t.closeEvent = lambda e, x=t: self.close_window(e, x)
            t.setParent(None, Qt.WindowType.Window)
            t.show()
        elif type(t) is GitTab:
            self.editor_tabs.removeTab(tab)
            t.closeEvent = lambda e, x=t: self.close_window(e, x)
            t.setParent(None, Qt.WindowType.Window)
            t.show()

    def presentation_mode(self) -> None:
        """Show current tab fullscreen"""
        t: EditorTab | GitTab | QWidget = self.editor_tabs.currentWidget()
        if type(t) is not EditorTab:
            return
        self.editor_tabs.removeTab(self.editor_tabs.currentIndex())
        t.contextMenuEvent = TextEditFullscreenMenu(t)
        t.closeEvent = lambda e, x=t: self.close_window(e, x)
        t.setParent(None, Qt.WindowType.Window)
        font: QFont = t.font()
        font.setPointSize(font.pointSize() * 2)
        t.setFont(font)
        t.showFullScreen()

    def close_window(self, e: QCloseEvent, widget: EditorTab) -> None:
        """Close windowed tab"""
        e.ignore()
        self.close_window_mode(widget)

    def close_window_mode(self, t: EditorTab | GitTab) -> None:
        """Return windowed tab to tab widget"""
        t.showNormal()
        t.closeEvent = EditorTab.closeEvent
        t.setWindowFlag(Qt.WindowType.Widget)
        if type(t) is EditorTab:
            t.setFont(self.settings.value('Font'))
            t.contextMenuEvent = TextEditMenu(t)
            self.editor_tabs.setCurrentIndex(self.editor_tabs.addTab(t, t.filename))
        else:
            self.editor_tabs.setCurrentIndex(self.editor_tabs.addTab(t, t.path.rsplit('/', maxsplit=1)[-1]))
        self.editor_tabs.setTabToolTip(self.editor_tabs.currentIndex(), t.path)

    def update_history(self) -> None:
        """Update history"""
        lst: list = [self.history.value(i) for i in self.history.allKeys()][-10:]
        self.history.clear()
        for i in range(len(lst)):
            self.history.setValue(str(i), lst[i])

    def update_history_menu(self) -> None:
        """Update history menu"""
        self.history_btn.clear()
        for item in self.history.allKeys():
            act: QAction = QAction(self.history.value(item).rsplit('/', maxsplit=1)[-1], self)
            act.setToolTip(self.history.value(item))
            act.triggered.connect(lambda: self.add_tab(self.sender().toolTip()))
            self.history_btn.addAction(act)
        self.history_btn.addSeparator()
        self.history_btn.addAction(self.delete_history_btn)

    def delete_history(self) -> None:
        """Delete history"""
        self.history.clear()
        self.update_history_menu()

    def select_language(self, language: str) -> None:
        """Translate program interface"""
        self.settings.setValue('Language', language)

        self.settings_window.setWindowTitle(texts.settings_btn[language])
        self.editor_tabs.empty_widget.setText(texts.open_btn[language])

        self.file_menu.setTitle(texts.file_menu[language])
        self.new_btn.setText(texts.new_btn[language])
        self.open_btn.setText(texts.open_btn[language])
        self.save_btn.setText(texts.save_btn[language])
        self.save_as_btn.setText(texts.save_as_btn[language])
        self.history_btn.setTitle(texts.history_btn[language])
        self.delete_history_btn.setText(texts.delete_history_btn[language])
        self.exit_btn.setText(texts.exit_btn[language])
        self.settings_btn.setText(texts.settings_btn[language])
        self.start_btn.setText(texts.start_btn[language])
        self.debug_btn.setText(texts.debug_btn[language])
        self.terminal_btn.setText(texts.terminal_btn[language])
        self.about_menu.setTitle(texts.about_menu[language])
        self.about_btn.setText(texts.about_btn[language])
        self.feedback_btn.setText(texts.feedback_btn[language])
        self.check_updates_btn.setText(texts.check_btn[language])
        self.download_btn.setText(texts.download_btn[language])
        self.view_menu.setTitle(texts.view_btn[language])
        self.monitor_btn.setText(texts.monitor_btn[language])
        self.presentation_btn.setText(texts.presentation_btn[language])
        self.edit_menu.setTitle(texts.edit_btn[language])
        self.undo.setText(texts.undo[language])
        self.redo.setText(texts.redo[language])
        self.cut.setText(texts.cut[language])
        self.copy.setText(texts.copy[language])
        self.paste.setText(texts.paste[language])
        self.select_all.setText(texts.select_all[language])
        self.find_btn.setText(texts.find_btn[language])

        self.settings_window.autorun.setText(texts.autorun[language])
        self.settings_window.autosave.setText(texts.autosave[language])
        self.settings_window.recent.setText(texts.recent[language])
        self.settings_window.tab_size.setPrefix(texts.tab_size[language])
        self.settings_window.style_select_group.setTitle(texts.style_select_group[language])
        self.settings_window.font_select_group.setTitle(texts.font_select_group[language])

    def select_style(self, style_name: str) -> None:
        """Set style to windows"""
        if style_name in style.keys():
            self.settings.setValue('Style', style_name)
            app.setStyleSheet(style[style_name])

    def select_font(self) -> None:
        """Change font for text edit area"""
        font: QFont = QFont(self.settings_window.fonts.currentText(), self.settings_window.font_size.value())
        self.settings.setValue('Font', font)
        for tab in self.editor_tabs.findChildren(EditorTab):
            tab.setFont(font)

    def autorun_check(self) -> None:
        """Set autorun settings"""
        self.settings.setValue('Autorun', int(self.settings_window.autorun.isChecked()))
        set_autorun(self.settings_window.autorun.isChecked())

    def start_terminal(self) -> None:
        """Open terminal window"""
        if sys.platform == 'win32':
            system('start "Vcode terminal" powershell')
        elif sys.platform.startswith('linux'):
            system('gnome-terminal')
        else:
            self.exit_code.setText('Can`t start terminal in this operating system')

    def start_program(self, file_ed: EditorTab = None) -> None:
        """Run code"""
        if file_ed is None or type(file_ed) is not EditorTab:
            file_ed = self.editor_tabs.currentWidget()
            if file_ed is None or type(file_ed) is not EditorTab:
                return
        if not self.settings.value('Autosave') and file_ed.saved_text != file_ed.toPlainText():
            button_text: str = WarningMessageBox(self, 'Warning', texts.save_warning, WarningMessageBox.SAVE).wait()
            if button_text in texts.cancel_btn.values():
                return
            elif button_text in texts.save_btn.values():
                file_ed.save()
        threading.Thread(target=self.program, args=[file_ed]).start()

    def debug_program(self, file_ed: EditorTab = None) -> None:
        """Debug code"""
        if file_ed is None or type(file_ed) is not EditorTab:
            file_ed = self.editor_tabs.currentWidget()
            if file_ed is None or type(file_ed) is not EditorTab:
                return
        if not self.settings.value('Autosave') and file_ed.saved_text != file_ed.toPlainText():
            button_text: str = WarningMessageBox(self, 'Warning', texts.save_warning, WarningMessageBox.SAVE).wait()
            if button_text in texts.cancel_btn.values():
                return
            elif button_text in texts.save_btn.values():
                file_ed.save()
        threading.Thread(target=self.program, args=[file_ed, True]).start()

    def program(self, code: EditorTab, debug: bool = False) -> None:
        """Code working process"""
        pth: str = code.path
        fnm: str = code.filename
        if code.language in language_list.keys():
            tid: str = str(threading.current_thread().native_id)
            command: str = code.start_command if not debug else code.debug_command
            if sys.platform == 'win32':
                with open(f'{USER}/.Vcode/process_{tid}.bat', 'w', encoding='utf-8') as bat_win32:
                    bat_win32.write(f'''
                              @echo off
                              chcp 65001>nul
                              cd {pth}
                              echo Interrupted > {fnm}.output
                              {command.format(filename=fnm)}
                              echo Exit code: %errorlevel% 
                              echo %errorlevel% > {fnm}.output
                              pause
                              ''')
                process: subprocess.Popen = subprocess.Popen(f'{USER}/.Vcode/process_{tid}.bat',
                                                             creationflags=subprocess.CREATE_NEW_CONSOLE,
                                                             process_group=subprocess.CREATE_NEW_PROCESS_GROUP)
                process.wait()
                remove(f'{USER}/.Vcode/process_{tid}.bat')
            elif sys.platform.startswith('linux'):
                with open(f'{USER}/.Vcode/process_{tid}.sh', 'w', encoding='utf-8') as bat_linux:
                    bat_linux.write(f'''
                              #!/bin/bash
                              cd {pth}
                              echo "Interrupted" > {fnm}.output
                              {command.format(filename=fnm)}
                              ec=$?
                              echo "Exit code: $ec"
                              echo $ec > {fnm}.output
                              read -r -p "Press enter to continue..." key
                              ''')
                system(f'chmod +x {resource_path(f"{USER}/.Vcode/process_{tid}.sh")}')
                process: subprocess.Popen = subprocess.Popen(resource_path(f"{USER}/.Vcode/process_{tid}.sh"),
                                                             shell=True)
                process.wait()
                remove(f'{USER}/.Vcode/process_{tid}.sh')
            else:
                with open(f'{pth}/{fnm}.output', 'w') as bat_w:
                    bat_w.write('Can`t start terminal in this operating system')
            with open(f'{pth}/{fnm}.output') as bat_output:
                if len(x := bat_output.readlines()) == 1:
                    self.exit_code.setText(f'Exit code: {x[0].rstrip()}')
                else:
                    self.exit_code.setText('Interrupted')
            remove(f'{pth}/{fnm}.output')
        else:
            self.exit_code.setText(f'Can`t start "{fnm}"')

    def save_file(self) -> None:
        """Save text to file"""
        if self.editor_tabs.count():
            self.editor_tabs.currentWidget().save()

    def new_file(self) -> None:
        """Create new file"""
        file: str = QFileDialog.getSaveFileName(directory=self.options.value('Folder') + '/untitled',
                                                filter=';;'.join(update_filters()))[0]
        if file:
            self.options.setValue('Folder', file.rsplit('/', maxsplit=1)[0])
            open(file, 'w', encoding=self.settings.value('Encoding')).close()
            self.add_tab(file)

    def open_file(self) -> None:
        """Open file"""
        file: str = QFileDialog.getOpenFileName(directory=self.options.value('Folder'),
                                                filter=';;'.join(update_filters()))[0]
        if file:
            self.options.setValue('Folder', file.rsplit('/', maxsplit=1)[0])
            self.add_tab(file)

    def save_as(self) -> None:
        """Save file as new file"""
        if self.editor_tabs.count():
            path, _ = QFileDialog.getSaveFileName(
                directory=self.options.value('Folder') + '/' + self.editor_tabs.currentWidget().filename,
                filter=';;'.join(update_filters()))
            if path:
                self.options.setValue('Folder', path.rsplit('/', maxsplit=1)[0])
                with open(path, 'w') as sf:
                    sf.write(self.editor_tabs.currentWidget().toPlainText())
                self.add_tab(path)

    def auto_save(self) -> None:
        """Save file when text changes"""
        if self.settings.value('Autosave'):
            self.editor_tabs.currentWidget().saved_text = self.editor_tabs.currentWidget().toPlainText()
            self.editor_tabs.currentWidget().save()

    def git_open(self) -> None:
        """Open git repository on computer"""
        if GIT_INSTALLED:
            path: str = QFileDialog.getExistingDirectory(directory=USER)
            if path:
                try:
                    if git.Repo(path).git_dir:
                        self.add_git_tab(path)
                except git.InvalidGitRepositoryError:
                    self.exit_code.setText(f'Not git repo {path}')
        else:
            self.exit_code.setText('Git not installed')

    def git_init(self) -> None:
        """Initialize new git repository"""
        if GIT_INSTALLED:
            path: str = QFileDialog.getExistingDirectory(directory=USER)
            if path:
                git.Repo.init(path)
                self.add_git_tab(path)
                self.exit_code.setText(f'Initialize repository {path}')
        else:
            self.exit_code.setText('Git not installed')

    def git_clone(self) -> None:
        """Clone git repository from url"""
        if GIT_INSTALLED:
            git_file: InputDialog = InputDialog('File', 'File', self)
            git_file.exec()
            if git_file.text_value():
                path: str = QFileDialog.getExistingDirectory(directory=USER)
                if path:
                    git.Repo.clone_from(git_file.text_value(), path)
        else:
            self.exit_code.setText('Git not installed')

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime: QMimeData = event.mimeData()
        if mime.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Open files from drop event"""
        for url in event.mimeData().urls():
            self.add_tab(url.toString().replace('file:///', ''))
        return super().dropEvent(event)

    def closeEvent(self, a0: QCloseEvent) -> None:
        """Save all settings when close"""
        for wgt in app.allWidgets():
            if type(wgt) is EditorTab and wgt.saved_text != wgt.toPlainText():
                button_text: str = WarningMessageBox(self, 'Warning', texts.save_warning, WarningMessageBox.SAVE).wait()
                if button_text in texts.cancel_btn.values():
                    a0.ignore()
                    return
                elif button_text in texts.save_btn.values():
                    for stab in app.findChildren(EditorTab):
                        stab.save()
                    a0.accept()
                else:
                    a0.accept()
                break
        save_last: QSettings = QSettings('Vcode', 'Last')
        for tab in filter(lambda w: type(w) is EditorTab, app.allWidgets()):
            if self.editor_tabs.indexOf(tab) == -1:
                tab.close()
            save_last.setValue('V' + tab.file, self.editor_tabs.indexOf(tab))
        for tab in self.editor_tabs.findChildren(GitTab):
            save_last.setValue('G' + tab.path, self.editor_tabs.indexOf(tab))
        save_last.setValue('current', self.editor_tabs.currentIndex())
        self.options.setValue('Splitter', self.splitter.sizes())
        if self.isMaximized():
            self.options.setValue('Geometry', 'Maximized')
        else:
            self.options.setValue('Geometry', self.geometry())


class SettingsDialog(QDialog):
    """Settings window"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setModal(True)

        self.style_select_group: QGroupBox = QGroupBox(self)
        self.style_select_layout: QVBoxLayout = QVBoxLayout()
        self.style_select_group.setLayout(self.style_select_layout)

        self.font_select_group: QGroupBox = QGroupBox(self)
        self.font_select_layout: QHBoxLayout = QHBoxLayout()
        self.font_select_group.setLayout(self.font_select_layout)

        self.fonts: QComboBox = QComboBox(self)
        self.fonts.addItems(QFontDatabase.families())
        self.font_select_layout.addWidget(self.fonts)

        self.font_size: QSpinBox = QSpinBox(self)
        self.font_size.setMinimum(1)
        self.font_size.setMaximum(400)
        self.font_select_layout.addWidget(self.font_size)

        self.check_boxes_group: QWidget = QWidget(self)
        self.check_boxes_layout: QVBoxLayout = QVBoxLayout()
        self.check_boxes_group.setLayout(self.check_boxes_layout)

        self.language: QComboBox = QComboBox(self)
        self.language.addItems(['EN', 'RU', 'DE', 'CH'])
        self.check_boxes_layout.addWidget(self.language)

        self.autorun: QCheckBox = QCheckBox(self)
        self.check_boxes_layout.addWidget(self.autorun)

        self.autosave: QCheckBox = QCheckBox(self)
        self.check_boxes_layout.addWidget(self.autosave)

        self.recent: QCheckBox = QCheckBox(self)
        self.check_boxes_layout.addWidget(self.recent)

        self.tab_size: QSpinBox = QSpinBox(self)
        self.tab_size.setMinimum(1)
        self.tab_size.setMaximum(16)
        self.check_boxes_layout.addWidget(self.tab_size)

        self.encoding: QComboBox = QComboBox(self)
        self.encoding.addItems(ENCODINGS)
        self.check_boxes_layout.addWidget(self.encoding)

        self.languages_list: QListWidget = QListWidget(self)
        self.languages_list.contextMenuEvent = self.languages_context_menu
        for lang in language_list.keys():
            self.languages_list.addItem(QListWidgetItem(lang, self.languages_list))
        self.languages_list.clicked.connect(self.language_settings)

        self.m_lay: QGridLayout = QGridLayout(self)
        self.m_lay.addWidget(self.style_select_group, 0, 0, 1, 1)
        self.m_lay.addWidget(self.check_boxes_group, 0, 1, 1, 1)
        self.m_lay.addWidget(self.font_select_group, 1, 0, 1, 3)
        self.m_lay.addWidget(self.languages_list, 0, 2, 1, 1)
        self.setLayout(self.m_lay)

        self.remove_btn: QAction = QAction(self)
        self.remove_btn.triggered.connect(self.remove_language)

        self.add_btn: QAction = QAction(self)
        self.add_btn.triggered.connect(self.add_language)

    def language_settings(self) -> None:
        """Open settings of language"""
        lsd: LanguageSettingsDialog = LanguageSettingsDialog(self.languages_list.currentItem().text(), self)
        lsd.setWindowTitle(f'{self.languages_list.currentItem().text()} - Vcode languages')
        lsd.exec()

    def languages_context_menu(self, event: QContextMenuEvent) -> None:
        """Custom context menu for language list"""
        menu: QMenu = QMenu(self)
        item: QListWidgetItem = self.languages_list.itemAt(event.pos())
        if item:
            self.remove_btn.setText(texts.remove_btn[QSettings('Vcode', 'Settings').value('Language')])
            menu.addAction(self.remove_btn)
            if item.text() in ['Python', 'Html', 'JSON']:
                menu.setEnabled(False)
        else:
            self.add_btn.setText(texts.add_btn[QSettings('Vcode', 'Settings').value('Language')])
            menu.addAction(self.add_btn)
        menu.popup(event.globalPos())

    def remove_language(self) -> None:
        """Remove a language"""
        name: QListWidgetItem = self.languages_list.selectedItems()[0]
        del language_list[name.text()]
        with open(USER + '/.Vcode/languages.json', 'w') as llfw:
            json.dump(language_list, llfw)
        self.languages_list.takeItem(self.languages_list.row(name))

    def add_language(self) -> None:
        """Add new language"""
        name: InputDialog = InputDialog('Name', 'Enter name:', self)
        name.exec()
        if name.text_value():
            language_list[name.text_value()] = {"highlight": "", "file_formats": [], "start_command": ""}
            with open(USER + '/.Vcode/languages.json', 'w') as llfw:
                json.dump(language_list, llfw)
        self.languages_list.addItem(QListWidgetItem(name.text_value(), self.languages_list))


class AboutDialog(QDialog):
    """Dialog about program"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setModal(True)
        self.setWindowTitle(f'Vcode v{VERSION}')
        self.setMinimumSize(250, 200)
        layout: QVBoxLayout = QVBoxLayout()
        self.setLayout(layout)

        self.icon: QLabel = QLabel(self)
        self.icon.setPixmap(QPixmap(resource_path('Vcode.ico')).scaled(128, 128))
        self.icon.resize(128, 128)
        layout.addWidget(self.icon, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.name: QLabel = QLabel('Vcode', self)
        self.name.setFont(QFont('Arial', 18))
        layout.addWidget(self.name, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.text: QLabel = QLabel(f'Version: {VERSION}<br><br><a href="https://vcodeide.ru">vcodeide.ru</a>'
                                   f'<br><br>Vladimir Varenik<br>'
                                   f'Copyright 2023-2024. All rights reserved<br>'
                                   f'This program is under GNU General Public License', self)
        self.text.setOpenExternalLinks(True)
        layout.addWidget(self.text)

        self.license: QPushButton = QPushButton('Read license', self)
        self.license.clicked.connect(lambda: startfile(resource_path('LICENSE')))
        layout.addWidget(self.license)

        self.text2: QLabel = QLabel('This program powered by PyQt6', self)
        layout.addWidget(self.text2)


class LanguageSettingsDialog(QDialog):
    """Settings of programming languages"""

    def __init__(self, language: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setMinimumSize(400, 250)
        self.language: str = language
        layout: QGridLayout = QGridLayout(self)
        self.setLayout(layout)
        self.lang_s: QSettings = QSettings('Vcode', 'Settings').value('Language')

        self.highlight: QLineEdit = QLineEdit(language_list[self.language]['highlight'], self)
        self.highlight.setPlaceholderText('Highlight file path')
        self.highlight.contextMenuEvent = LineEditMenu(self.highlight)
        layout.addWidget(self.highlight, 0, 0, 1, 6)

        self.file_formats: QLineEdit = QLineEdit(' '.join(language_list[self.language]['file_formats']), self)
        self.file_formats.setPlaceholderText('Supported file formats')
        self.file_formats.contextMenuEvent = LineEditMenu(self.file_formats)
        layout.addWidget(self.file_formats, 1, 0, 1, 6)

        self.start_command: QLineEdit = QLineEdit(language_list[self.language]['start_command'], self)
        self.start_command.setPlaceholderText('Start command')
        self.start_command.contextMenuEvent = LineEditMenu(self.start_command)
        layout.addWidget(self.start_command, 2, 0, 1, 6)

        self.debug_command: QLineEdit = QLineEdit(language_list[self.language]['debug_command'], self)
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
        a, _ = QFileDialog.getOpenFileName(self, directory=USER, filter='Highlight files (*.hl)')
        if a:
            self.highlight.setText(a)

    def find_compiler(self):
        """Search compiler in files"""
        a, _ = QFileDialog.getOpenFileName(
            self, directory=USER, filter='Executable files (*.exe);;Shell files (*.sh *.bat *.vbs);;All files (*.*)')
        if a:
            self.start_command.setText(f'"{a}" "{{filename}}"')

    def find_debugger(self):
        """Search debugger in files"""
        a, _ = QFileDialog.getOpenFileName(
            self, directory=USER, filter='Executable files (*.exe);;Shell files (*.sh *.bat *.vbs);;All files (*.*)')
        if a:
            self.start_command.setText(f'"{a}" "{{filename}}"')

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
        language_list[self.language]: dict[str, str] = {'highlight': self.highlight.text(),
                                                        'file_formats': [f for f in self.file_formats.text().split()],
                                                        'start_command': self.start_command.text()}
        with open(USER + '/.Vcode/languages.json', 'w') as llfw:
            json.dump(language_list, llfw)
        self.accept()


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
        if highlighter.startswith(USER + '/.Vcode/highlights') and highlighter.endswith(
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
            for hms in self.findChildren(HighlightMakerString):
                hlf.write(hms.rstring.text() + ' = {' + hms.json_params.text() + '};\n')

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


if __name__ == '__main__':
    app: QApplication = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('Vcode.ico')))
    ide: IdeWindow = IdeWindow()
    ide.settings_window.autorun.setEnabled(False)
    ide.settings_window.autorun.setStyleSheet('font: italic;')
    if ide.settings.value('Recent') == 1:
        last: QSettings = QSettings('Vcode', 'Last')
        for n in last.allKeys():
            if n != 'current' and last.value(n) is not None:
                if n[0] == 'V':
                    ide.add_tab(n[1:], int(last.value(n)))
                elif n[0] == 'G':
                    ide.add_git_tab(n[1:], int(last.value(n)))
            elif last.value('current') is not None:
                ide.editor_tabs.setCurrentIndex(int(last.value('current')))
        last.clear()
    for arg in sys.argv[1:]:
        if isfile(arg):
            if not arg.endswith('.hl'):
                ide.add_tab(arg.replace('\\', '/'))
            else:
                hm: HighlightMaker = HighlightMaker(arg)
                hm.setWindowTitle(f'{arg} - Vcode highlight maker')
                hm.exec()
    sys.exit(app.exec())
