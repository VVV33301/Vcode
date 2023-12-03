import os
import sys
import subprocess
import threading
import re
import json
import shutil
from webbrowser import open as openweb
from os.path import isfile, isdir, dirname, abspath, join, exists, expanduser
from requests import get
import psutil
import git

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import texts
from style import STYLE

VERSION = '0.6.0'


def resource_path(relative_path: str) -> str:
    return join(getattr(sys, '_MEIPASS', dirname(abspath(sys.argv[0]))), relative_path)


def set_autorun(enabled: bool) -> None:
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
    filters_f: list = ['All Files (*.*)']
    for i, j in language_list.items():
        filters_f.append(f'{i} Files (*.{" *.".join(j["file_formats"])})')
    return filters_f


encodings: list[str] = ['ascii', 'big5', 'big5hkscs', 'cp037', 'cp1006', 'cp1026', 'cp1125', 'cp1140', 'cp1250',
                        'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256', 'cp1257', 'cp1258', 'cp273',
                        'cp424', 'cp437', 'cp500', 'cp720', 'cp737', 'cp775', 'cp850', 'cp852', 'cp855', 'cp856',
                        'cp857', 'cp858', 'cp860', 'cp861', 'cp862', 'cp863', 'cp864', 'cp865', 'cp866', 'cp869',
                        'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 'euc_jis_2004', 'euc_jisx0213', 'euc_jp', 'euc_kr',
                        'gb18030', 'gb2312', 'gbk', 'hz', 'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2',
                        'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext', 'iso2022_kr', 'iso8859-1', 'iso8859-10',
                        'iso8859-11', 'iso8859-13', 'iso8859-14', 'iso8859-15', 'iso8859-16', 'iso8859-2', 'iso8859-3',
                        'iso8859-4', 'iso8859-5', 'iso8859-6', 'iso8859-7', 'iso8859-8', 'iso8859-9', 'johab', 'koi8-r',
                        'koi8-t', 'koi8-u', 'kz1048', 'mac-cyrillic', 'mac-greek', 'mac-iceland', 'mac-latin2',
                        'mac-roman', 'mac-turkish', 'ptcp154', 'shift_jis', 'shift_jis_2004', 'shift_jisx0213',
                        'utf-16', 'utf-16-be', 'utf-16-le', 'utf-32', 'utf-32-be', 'utf-32-le', 'utf-7', 'utf-8',
                        'utf-8-sig']
if exists(resource_path('languages.json')):
    with open(resource_path('languages.json')) as llf:
        language_list: dict[str, dict[str, str]] = json.load(llf)
else:
    language_list: dict[str, dict[str, str]] = {
        "Python": {
            "highlight": "highlights/python.hl",
            "file_formats": ["py", "pyw", "pyi"],
            "start_command": "python \"{filename}\""
        },
        "Html": {
            "highlight": "highlights/html.hl",
            "file_formats": ["htm", "html"],
            "start_command": "start \"\" \"{filename}\""
        }
    }
    with open(resource_path('languages.json'), 'w') as llf:
        json.dump(language_list, llf)


class Highlighter(QSyntaxHighlighter):
    def __init__(self, highlight_path: str, parent: QTextDocument = None) -> None:
        super().__init__(parent)
        self.mapping: dict[str, QTextCharFormat] = {}
        self.tab_words: list[str] = []
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
                self.mapping[rf'{expression}']: QTextCharFormat = text_char

    def highlightBlock(self, text: str) -> None:
        for pattern, char in self.mapping.items():
            for match in re.finditer(pattern, text, re.MULTILINE):
                s, e = match.span()
                self.setFormat(s, e - s, char)


class TextEditMenu(QMenu):
    """Custom QTextEdit Menu"""

    def __init__(self, parent: QTextEdit | QPlainTextEdit, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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

        self.start: QAction = QAction(self)
        self.start.triggered.connect(ide.start_program)
        self.start.setShortcut(QKeySequence.StandardKey.Refresh)
        self.addAction(self.start)

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
        self.start.setText(texts.start_btn[lang])
        self.search.setTitle(texts.search[lang])
        self.search_in_g.setText(texts.search_in_g[lang])
        self.search_in_so.setText(texts.search_in_so[lang])
        self.popup(event.globalPos())


class TreeViewMenu(QMenu):
    """Custom QTreeView Menu"""

    def __init__(self, parent: QTreeView, parent_class, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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

        self.lang_s: QSettings = QSettings('Vcode', 'Settings')

    def __call__(self, event: QContextMenuEvent) -> None:
        lang: str = self.lang_s.value('Language')
        self.new_btn.setText(texts.new_btn[lang])
        self.copy_btn.setText(texts.copy[lang])
        self.paste_btn.setText(texts.paste[lang])
        self.delete_btn.setText(texts.delete_btn[lang])
        self.rename_btn.setText(texts.rename_btn[lang])
        self.popup(event.globalPos())

    def new_file(self) -> None:
        file: QInputDialog = QInputDialog(self)
        file.exec()
        if file.textValue():
            if file.textValue().endswith(('/', '\\')):
                os.mkdir(self.c.model.filePath(self.c.tree.selectedIndexes()[0]) + '/' + file.textValue())
            else:
                x: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0]) + '/' + file.textValue()
                open(x, 'w', encoding=self.lang_s.value('Encoding')).close()
                self.c.add_tab(x)

    def copy_file(self) -> None:
        n: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0])
        if (isfile(n) or isdir(n)) and sys.platform == 'win32':
            os.system(f'powershell -command "Set-Clipboard -Path "{n}""')

    def paste_file(self) -> None:
        path: str = app.clipboard().mimeData().urls()[0].url().replace('file:///', '')
        new_path = self.c.model.filePath(self.c.tree.selectedIndexes()[0])
        if isdir(new_path):
            if isfile(path):
                shutil.copy2(path, new_path + '/' + app.clipboard().mimeData().urls()[0].fileName())
            elif isdir(path):
                shutil.copytree(path, new_path + '/' + path.rsplit('/', maxsplit=1)[-1])

    def delete_file(self) -> None:
        n: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0])
        if isfile(n):
            os.remove(n)
        elif isdir(n):
            shutil.rmtree(n)

    def rename_file(self) -> None:
        file: QInputDialog = QInputDialog(self)
        path, name = self.c.model.filePath(self.c.tree.selectedIndexes()[0]).rsplit('/', maxsplit=1)
        file.setTextValue(name)
        file.exec()
        if file.textValue() != name:
            try:
                os.rename(path + '/' + name, path + '/' + file.textValue())
            except Exception:
                pass


class LineEditMenu(QMenu):
    """Custom QLineEdit QMenu"""

    def __init__(self, parent: QLineEdit, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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
        """Call this class to get contect menu"""
        lang: str = self.lang_s.value('language')
        self.undo.setText(texts.undo[lang])
        self.redo.setText(texts.redo[lang])
        self.cut.setText(texts.cut[lang])
        self.copy.setText(texts.copy[lang])
        self.paste.setText(texts.paste[lang])
        self.select_all.setText(texts.select_all[lang])
        self.popup(event.globalPos())


class SystemMonitor(QWidget):
    def __init__(self, pid: int):
        super().__init__()
        while True:
            print(psutil.Process(pid).cpu_percent())


class GitTab(QWidget):
    def __init__(self, path: str, parent_exit_code_label: QLabel | None = None):
        if not self.git_check():
            raise Exception('Git not installed')
        super().__init__()
        self.path: str = path

        if parent_exit_code_label is not None:
            self.exit_code: QLabel = parent_exit_code_label
        else:
            self.exit_code: QLabel = QLabel()

        self.git_repo: git.Repo = git.Repo(path)

        self.lay: QGridLayout = QGridLayout(self)

        self.branch: QComboBox = QComboBox(self)
        self.branch.addItems([i.name for i in self.git_repo.branches])
        self.branch.setCurrentText(self.git_repo.active_branch.name)
        self.branch.currentTextChanged.connect(lambda: self.change_branch(self.branch.currentText()))
        self.lay.addWidget(self.branch)

        self.repo_list: QTreeView = QTreeView(self)
        self.repo_list.contextMenuEvent = TreeViewMenu(self.repo_list, self)
        self.repo_list_model: QFileSystemModel = QFileSystemModel(self)
        self.repo_list_model.setRootPath(path)
        self.repo_list.setModel(self.repo_list_model)
        self.repo_list.setRootIndex(self.repo_list_model.index(path))
        self.lay.addWidget(self.repo_list)

    def git_check(self):
        try:
            subprocess.run('git -v')
            return True
        except FileNotFoundError:
            self.exit_code.setText('Git not installed')
            return False

    def change_branch(self, branch: str):
        self.git_repo.head.reference = branch
        self.git_repo.head.reset(working_tree=True)

    def git_commit(self):
        git_descr: QInputDialog = QInputDialog(self)
        git_descr.exec()
        if git_descr.textValue():
            '''p: subprocess.Popen = subprocess.Popen(f'git commit -m "{git_descr.textValue()}" {self.path}',
                                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
            if p.returncode:
                self.exit_code.setText(p.stdout.read().decode(sys.stdin.encoding).strip())
            else:
                self.exit_code.setText(f'Commit repository {self.path}')'''
            for i in self.repo_list.selectedIndexes():
                self.git_repo.index.add(self.repo_list_model.filePath(i))
            self.git_repo.index.commit(git_descr.textValue())

    def git_push(self):
        self.git_repo.remotes.origin.push()


class EditorTab(QPlainTextEdit):
    """Editor text place"""

    def __init__(self, file: str, parent: QWidget = None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.p: QWidget = parent

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
            self.setPlainText('Unsupported encoding')
            self.setReadOnly(True)
            self.save = lambda: None
            self.line_num.setVisible(False)
        self.saved_text: str = self.toPlainText()
        self.highlighter: Highlighter | None = None
        self.start_command: str | None = None
        self.language: str = ''

    def set_highlighter(self, highlighter: Highlighter) -> None:
        self.highlighter: Highlighter = highlighter
        self.highlighter.setDocument(self.document())

    def save(self) -> None:
        with open(self.file, 'w', encoding=self.pr_settings.value('Encoding')) as sf:
            sf.write(self.toPlainText())
        self.saved_text: str = self.toPlainText()

    def line_number_area_width(self) -> int:
        return max(45, 5 + self.fontMetrics().boundingRect('9').width() * (len(str(self.blockCount())) + 3))

    def update_line_number_area_width(self) -> None:
        self.setViewportMargins(self.line_number_area_width() + 7, 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_num.scroll(0, dy)
        else:
            self.line_num.update(0, rect.y(), self.line_num.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        cr: QRect = self.contentsRect()
        self.line_num.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def update_line_event(self, event: QPaintEvent) -> None:
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

    def keyPressEvent(self, e: QKeyEvent) -> None:
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

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        pass

    def dropEvent(self, e: QDropEvent) -> None:
        mime: QMimeData = e.mimeData()
        if mime.hasUrls():
            self.p.dropEvent(e)
        elif mime.hasText():
            super().dropEvent(e)
        else:
            e.ignore()


class LineNumberArea(QWidget):
    """Area for numbers of lines"""

    def __init__(self, editor: EditorTab):
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

    def empty(self) -> None:
        if not self.count():
            self.empty_widget.setVisible(True)
        else:
            self.empty_widget.setVisible(False)


class HighlightMakerString(QWidget):
    """Editor string for highlight maker"""

    def __init__(self, rstring, params) -> None:
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

        self.about_window: AboutDialog = AboutDialog(self)

        self.settings_window: SettingsDialog = SettingsDialog(self)
        for st in STYLE.keys():
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
        self.start_btn.setShortcut(QKeySequence.StandardKey.Refresh)
        self.start_btn.triggered.connect(self.start_program)
        self.tool_bar.addAction(self.start_btn)

        self.terminal_btn: QAction = QAction(self)
        self.terminal_btn.triggered.connect(self.start_terminal)
        self.tool_bar.addAction(self.terminal_btn)

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
        self.save_btn.triggered.connect(self.save_file)
        self.file_menu.addAction(self.save_btn)

        self.save_as_btn: QAction = QAction(self)
        self.save_as_btn.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_btn.triggered.connect(self.save_as)
        self.file_menu.addAction(self.save_as_btn)

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
        self.about_btn.triggered.connect(self.about_window.exec)
        self.about_menu.addAction(self.about_btn)

        self.feedback_btn: QAction = QAction(self)
        self.feedback_btn.triggered.connect(lambda: openweb('https://vcode.rf.gd/feedback'))
        self.about_menu.addAction(self.feedback_btn)

        self.download_btn: QAction = QAction(self)
        self.download_btn.triggered.connect(lambda: openweb('https://vcode.rf.gd/download'))

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
            self.options.setValue('Folder', expanduser('~'))
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

        if self.options.value('Geometry') == 'Maximized':
            self.showMaximized()
        elif self.options.value('Geometry') == 'Not init':
            self.resize(1000, 700)
            self.show()
        else:
            self.setGeometry(self.options.value('Geometry'))
            self.show()

        self.check_updates()

    def check_updates(self) -> None:
        def check():
            try:
                if VERSION not in get('https://github.com/VVV33301/Vcode/releases/latest').text.split('title>')[1]:
                    self.menuBar().addAction(self.download_btn)
            except OSError:
                pass

        threading.Thread(target=check).start()

    def sel_tab(self) -> None:
        if self.editor_tabs.count():
            self.setWindowTitle(self.editor_tabs.tabText(self.editor_tabs.currentIndex()) + ' - Vcode')
            if type(self.editor_tabs.currentWidget()) == EditorTab:
                d: list[str] = self.editor_tabs.currentWidget().file.split('/')
                for _ in range(len(d)):
                    self.tree.setExpanded(self.model.index('/'.join(d)), True)
                    del d[-1]
                self.tree.selectionModel().select(self.model.index(self.editor_tabs.currentWidget().file),
                                                  QItemSelectionModel.SelectionFlag.Select)
            else:
                self.tree.selectionModel().select(self.model.index(self.editor_tabs.currentWidget().path),
                                                  QItemSelectionModel.SelectionFlag.Select)
        else:
            self.setWindowTitle('Vcode')

    def add_tab(self, filename: str, row: int | None = None) -> None:
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
        c: QTextCursor = editor.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)
        editor.setTextCursor(c)
        editor.setFocus()
        editor.cursorPositionChanged.connect(editor.highlight_current_line)
        for langname, language in language_list.items():
            if filename.rsplit('.', maxsplit=1)[-1] in language['file_formats']:
                editor.set_highlighter(Highlighter(resource_path(language['highlight'])))
                editor.start_command = language['start_command']
                editor.language = langname
        if row is None:
            self.editor_tabs.setCurrentIndex(self.editor_tabs.addTab(editor, editor.filename))
        else:
            self.editor_tabs.setCurrentIndex(self.editor_tabs.insertTab(row, editor, editor.filename))
        self.editor_tabs.setTabToolTip(self.editor_tabs.currentIndex(), editor.file)

    def add_git_tab(self, path: str, row: int | None = None) -> None:
        if not isdir(path):
            return
        editor: GitTab = GitTab(path, self.exit_code)
        if row is None:
            self.editor_tabs.setCurrentIndex(self.editor_tabs.addTab(editor, path.split('/')[-1]))
        else:
            self.editor_tabs.setCurrentIndex(self.editor_tabs.insertTab(row, editor, path.split('/')[-1]))
        self.editor_tabs.setTabToolTip(self.editor_tabs.currentIndex(), path)

    def close_tab(self, tab: int) -> None:
        widget: EditorTab | GitTab = self.editor_tabs.widget(tab)
        if type(widget) is EditorTab:
            if widget.saved_text != widget.toPlainText():
                button: QMessageBox.StandardButton = QMessageBox.warning(
                    self, 'Warning', texts.save_warning[self.settings.value('Language')],
                    buttons=QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard |
                            QMessageBox.StandardButton.Cancel,
                    defaultButton=QMessageBox.StandardButton.Save)
                if button == QMessageBox.StandardButton.Cancel:
                    return
                elif button == QMessageBox.StandardButton.Save:
                    widget.save()
        self.editor_tabs.removeTab(tab)
        widget.deleteLater()

    def select_language(self, language: str) -> None:
        self.settings.setValue('Language', language)

        self.settings_window.setWindowTitle(texts.settings_window[language])
        self.editor_tabs.empty_widget.setText(texts.open_btn[language])

        self.file_menu.setTitle(texts.file_menu[language])
        self.new_btn.setText(texts.new_btn[language])
        self.open_btn.setText(texts.open_btn[language])
        self.save_btn.setText(texts.save_btn[language])
        self.save_as_btn.setText(texts.save_as_btn[language])
        self.settings_btn.setText(texts.settings_btn[language])
        self.start_btn.setText(texts.start_btn[language])
        self.terminal_btn.setText(texts.terminal_btn[language])
        self.about_menu.setTitle(texts.about_menu[language])
        self.about_btn.setText(texts.about_btn[language])
        self.feedback_btn.setText(texts.feedback_btn[language])
        self.download_btn.setText(texts.download_btn[language])

        self.settings_window.autorun.setText(texts.autorun[language])
        self.settings_window.autosave.setText(texts.autosave[language])
        self.settings_window.recent.setText(texts.recent[language])
        self.settings_window.tab_size.setPrefix(texts.tab_size[language])
        self.settings_window.style_select_group.setTitle(texts.style_select_group[language])
        self.settings_window.font_select_group.setTitle(texts.font_select_group[language])

    def select_style(self, style_name: str) -> None:
        if style_name in STYLE.keys():
            self.settings.setValue('Style', style_name)
            self.setStyleSheet(STYLE[style_name])

    def select_font(self) -> None:
        font: QFont = QFont(self.settings_window.fonts.currentText(), self.settings_window.font_size.value())
        self.settings.setValue('Font', font)
        for tab in self.editor_tabs.findChildren(EditorTab):
            tab.setFont(font)

    def autorun_check(self) -> None:
        self.settings.setValue('Autorun', int(self.settings_window.autorun.isChecked()))
        set_autorun(self.settings_window.autorun.isChecked())

    def start_terminal(self) -> None:
        if sys.platform == 'win32':
            os.system('start "Vcode terminal" powershell')
        elif sys.platform.startswith('linux'):
            os.system('gnome-terminal')
        else:
            self.exit_code.setText('Can`t start terminal in this operating system')

    def start_program(self) -> None:
        if self.editor_tabs.count():
            if not self.settings.value('Autosave') and \
                    self.editor_tabs.currentWidget().saved_text != self.editor_tabs.currentWidget().toPlainText():
                button: QMessageBox.StandardButton = QMessageBox.warning(
                    self, 'Warning', texts.save_warning[self.settings.value('Language')],
                    buttons=QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
                    defaultButton=QMessageBox.StandardButton.Save)
                if button == QMessageBox.StandardButton.Cancel:
                    return
                else:
                    self.editor_tabs.currentWidget().save()
            threading.Thread(target=self.program).start()

    def program(self) -> None:
        code: EditorTab = self.editor_tabs.currentWidget()
        pth: str = code.path
        fnm: str = code.filename
        if code.language in language_list.keys():
            tid: str = str(threading.current_thread().native_id)
            if sys.platform == 'win32':
                with open(f'process_{tid}.bat', 'w', encoding='utf-8') as bat_win32:
                    bat_win32.write(f'''
                              @echo off
                              chcp 65001>nul
                              cd {pth}
                              echo Interrupted > {fnm}.output
                              {code.start_command.format(filename=fnm)}
                              echo Exit code: %errorlevel% 
                              echo %errorlevel% > {fnm}.output
                              pause
                              ''')
                process: subprocess.Popen = subprocess.Popen(f'process_{tid}.bat',
                                                             creationflags=subprocess.CREATE_NEW_CONSOLE,
                                                             process_group=subprocess.CREATE_NEW_PROCESS_GROUP)
                SystemMonitor(process.pid)
                process.wait()
                os.remove(f'process_{tid}.bat')
            elif sys.platform.startswith('linux'):
                with open(f'process_{tid}.sh', 'w', encoding='utf-8') as bat_linux:
                    bat_linux.write(f'''
                              #!/bin/bash
                              cd {pth}
                              echo "Interrupted" > {fnm}.output
                              {code.start_command.format(filename=fnm)}
                              ec=$?
                              echo "Exit code: $ec"
                              echo $ec > {fnm}.output
                              read -r -p "Press enter to continue..." key
                              ''')
                os.system(f'chmod +x {resource_path(f"process_{tid}.sh")}')
                process: subprocess.Popen = subprocess.Popen(resource_path(f"process_{tid}.sh"), shell=True)
                process.wait()
                os.remove(f'process_{tid}.sh')
            else:
                with open(f'{pth}/{fnm}.output', 'w') as bat_w:
                    bat_w.write('Can`t start terminal in this operating system')
            with open(f'{pth}/{fnm}.output') as bat_output:
                if len(x := bat_output.readlines()) == 1:
                    self.exit_code.setText(f'Exit code: {x[0].rstrip()}')
                else:
                    self.exit_code.setText('Interrupted')
            os.remove(f'{pth}/{fnm}.output')
        else:
            self.exit_code.setText(f'Can`t start "{fnm}"')

    def save_file(self) -> None:
        if self.editor_tabs.count():
            self.editor_tabs.currentWidget().save()

    def new_file(self) -> None:
        file, _ = QFileDialog.getSaveFileName(directory=self.options.value('Folder') + '/untitled',
                                              filter=';;'.join(update_filters()))
        if file:
            self.options.setValue('Folder', file.rsplit('/', maxsplit=1)[0])
            open(file, 'w', encoding=self.settings.value('Encoding')).close()
            self.add_tab(file)

    def open_file(self) -> None:
        file, _ = QFileDialog.getOpenFileName(directory=self.options.value('Folder'),
                                              filter=';;'.join(update_filters()))
        if file:
            self.options.setValue('Folder', file.rsplit('/', maxsplit=1)[0])
            self.add_tab(file)

    def save_as(self) -> None:
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
        if self.settings.value('Autosave'):
            self.editor_tabs.currentWidget().saved_text = self.editor_tabs.currentWidget().toPlainText()
            self.editor_tabs.currentWidget().save()

    def git_check(self):
        try:
            subprocess.run('git -v')
            return True
        except FileNotFoundError:
            self.exit_code.setText('Git not installed')
            return False

    def git_open(self):
        if self.git_check():
            path: str = QFileDialog.getExistingDirectory(directory=os.path.expanduser('~'))
            if path:
                '''p: subprocess.Popen = subprocess.Popen(f'git -C {path} status',
                                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                p.wait()
                if p.returncode:
                    self.exit_code.setText(p.stdout.read().decode(sys.stdin.encoding).strip())
                else:
                    self.add_git_tab(path)'''
                try:
                    if git.Repo(path).git_dir:
                        self.add_git_tab(path)
                except git.InvalidGitRepositoryError:
                    self.exit_code.setText(f'Not git repo {path}')

    def git_init(self):
        if self.git_check():
            path: str = QFileDialog.getExistingDirectory(directory=os.path.expanduser('~'))
            if path:
                '''p: subprocess.Popen = subprocess.Popen(f'git init {path}',
                                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                p.wait()
                if p.returncode:
                    self.exit_code.setText(p.stdout.read().decode(sys.stdin.encoding).strip())
                else:
                    self.add_git_tab(path)
                    self.exit_code.setText(f'Initialize repository {path}')'''
                git.Repo.init(path)
                self.add_git_tab(path)
                self.exit_code.setText(f'Initialize repository {path}')

    def git_clone(self):
        if self.git_check():
            git_file: QInputDialog = QInputDialog(self)
            git_file.exec()
            if git_file.textValue():
                path: str = QFileDialog.getExistingDirectory(directory=os.path.expanduser('~'))
                if path:
                    '''p: subprocess.Popen = subprocess.Popen(f'git clone {git_file.textValue()} {path}',
                                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    p.wait()
                    if p.returncode:
                        self.exit_code.setText(p.stdout.read().decode(sys.stdin.encoding).strip())
                    else:
                        self.exit_code.setText(f'Clone repository {git_file.textValue()}')'''
                    git.Repo.clone_from(git_file.textValue(), path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime: QMimeData = event.mimeData()
        if mime.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            self.add_tab(url.toString().replace('file:///', ''))
        return super().dropEvent(event)

    def closeEvent(self, a0: QCloseEvent) -> None:
        for tab in self.editor_tabs.findChildren(EditorTab):
            if tab.saved_text != tab.toPlainText():
                button: QMessageBox.StandardButton = QMessageBox.warning(
                    self, 'Warning', texts.save_warning[self.settings.value('Language')],
                    buttons=QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard |
                            QMessageBox.StandardButton.Cancel,
                    defaultButton=QMessageBox.StandardButton.Save)
                if button == QMessageBox.StandardButton.Cancel:
                    a0.ignore()
                elif button == QMessageBox.StandardButton.Save:
                    for stab in self.editor_tabs.findChildren(EditorTab):
                        stab.save()
                    a0.accept()
                else:
                    a0.accept()
                break
        save_last: QSettings = QSettings('Vcode', 'Last')
        for tab in self.editor_tabs.findChildren(EditorTab):
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
        self.encoding.addItems(encodings)
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
        lsd: LanguageSettingsDialog = LanguageSettingsDialog(self.languages_list.currentItem().text())
        lsd.setWindowTitle(f'{self.languages_list.currentItem().text()} - Vcode languages')
        lsd.exec()

    def languages_context_menu(self, event: QContextMenuEvent) -> None:
        menu: QMenu = QMenu(self)
        item: QListWidgetItem = self.languages_list.itemAt(event.pos())
        if item:
            self.remove_btn.setText(texts.remove_btn[QSettings('Vcode', 'Settings').value('Language')])
            menu.addAction(self.remove_btn)
        else:
            self.add_btn.setText(texts.add_btn[QSettings('Vcode', 'Settings').value('Language')])
            menu.addAction(self.add_btn)
        menu.popup(event.globalPos())

    def remove_language(self) -> None:
        name: QListWidgetItem = self.languages_list.selectedItems()[0]
        del language_list[name.text()]
        with open(resource_path('languages.json'), 'w') as llfw:
            json.dump(language_list, llfw)
        self.languages_list.takeItem(self.languages_list.row(name))

    def add_language(self) -> None:
        name: QInputDialog = QInputDialog(self)
        name.exec()
        if name.textValue():
            language_list[name.textValue()] = {"highlight": "", "file_formats": [], "start_command": ""}
            with open(resource_path('languages.json'), 'w') as llfw:
                json.dump(language_list, llfw)
        self.languages_list.addItem(QListWidgetItem(name.textValue(), self.languages_list))


class AboutDialog(QDialog):
    """Dialog about program"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setModal(True)
        self.setWindowTitle(f'Vcode v{VERSION}')
        self.setMinimumSize(250, 200)
        self.lay: QVBoxLayout = QVBoxLayout()

        self.icon: QLabel = QLabel(self)
        self.icon.setPixmap(QPixmap(resource_path('Vcode.ico')).scaled(128, 128))
        self.icon.resize(128, 128)
        self.lay.addWidget(self.icon, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.name: QLabel = QLabel('Vcode', self)
        self.name.setFont(QFont('Arial', 18))
        self.lay.addWidget(self.name, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.text: QLabel = QLabel(f'Version: {VERSION}\n\nVladimir Varenik\nAll rights reserved', self)
        self.lay.addWidget(self.text)

        self.setLayout(self.lay)


class LanguageSettingsDialog(QDialog):
    """Settings of programming languages"""

    def __init__(self, language: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.language: str = language
        layout: QGridLayout = QGridLayout(self)
        self.setLayout(layout)
        self.lang_s: QSettings = QSettings('Vcode', 'Settings')

        self.highlight: QLineEdit = QLineEdit(language_list[self.language]['highlight'], self)
        self.file_formats: QLineEdit = QLineEdit(' '.join(language_list[self.language]['file_formats']), self)
        self.start_command: QLineEdit = QLineEdit(language_list[self.language]['start_command'], self)

        self.highlight.contextMenuEvent = LineEditMenu(self.highlight)
        self.file_formats.contextMenuEvent = LineEditMenu(self.file_formats)
        self.start_command.contextMenuEvent = LineEditMenu(self.start_command)

        layout.addWidget(self.highlight, 0, 0, 1, 2)
        layout.addWidget(self.file_formats, 1, 0, 1, 2)
        layout.addWidget(self.start_command, 2, 0, 1, 2)

        self.edit_highlight_btn: QPushButton = QPushButton(texts.edit_highlight_btn[self.lang_s.value('Language')],
                                                           self)
        self.edit_highlight_btn.clicked.connect(self.highlight_maker_call)
        layout.addWidget(self.edit_highlight_btn, 3, 0, 1, 1)

        self.save_btn: QPushButton = QPushButton(texts.save_btn[self.lang_s.value('Language')], self)
        self.save_btn.clicked.connect(self.save_language)
        layout.addWidget(self.save_btn, 3, 1, 1, 1)

    def highlight_maker_call(self) -> None:
        hlm: HighlightMaker = HighlightMaker(language_list[self.language]['highlight'])
        hlm.setWindowTitle(f'{language_list[self.language]["highlight"].split("/")[-1]} - Vcode highlight maker')
        hlm.exec()

    def save_language(self) -> None:
        language_list[self.language]: dict[str, str] = {'highlight': self.highlight.text(),
                                                        'file_formats': [f for f in self.file_formats.text().split()],
                                                        'start_command': self.start_command.text()}
        with open(resource_path('languages.json'), 'w') as llfw:
            json.dump(language_list, llfw)


class HighlightMaker(QDialog):
    """Make and rewrite highlights"""

    def __init__(self, highlighter: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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

    def add_string(self) -> None:
        self.layout_hl.addWidget(HighlightMakerString('', '{}'))

    def save_highlighter(self) -> None:
        with open(self.highlighter, 'w') as hlf:
            for hms in self.findChildren(HighlightMakerString):
                hlf.write(hms.rstring.text() + ' = {' + hms.json_params.text() + '};\n')


if __name__ == '__main__':
    app: QApplication = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('Vcode.ico')))
    ide: IdeWindow = IdeWindow()
    ide.settings_window.autorun.setEnabled(False)
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
                ide.add_tab(arg)
            else:
                hm: HighlightMaker = HighlightMaker(arg)
                hm.setWindowTitle(f'{arg} - Vcode highlight maker')
                hm.exec()
    sys.exit(app.exec())
