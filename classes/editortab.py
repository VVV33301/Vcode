from PyQt6.QtWidgets import QPlainTextEdit, QPushButton, QCompleter, QTextEdit
from PyQt6.QtGui import (QResizeEvent, QPaintEvent, QPainter, QTextCursor, QColor, QKeyEvent, QDragEnterEvent,
                         QDropEvent, QPalette, QTextFormat, QTextBlock)
from PyQt6.QtCore import QSettings, Qt, QTimer, QRect, QMimeData
import re
from os import startfile
from .highlighter import Highlighter
from .linenumberarea import LineNumberArea
import texts


class EditorTab(QPlainTextEdit):
    """Editor text place"""

    def __init__(self, file: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

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

        self.autosave_timer: QTimer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save)

    def set_highlighter(self, highlighter: Highlighter) -> None:
        """Add highlighter to code"""
        self.highlighter: Highlighter = highlighter
        self.highlighter.setDocument(self.document())
        if self.highlighter.complete_words:
            self.completer: QCompleter = QCompleter(self.highlighter.complete_words, self)
            self.completer.setWidget(self)
            self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.completer.activated.connect(self.insert_completion)

    def save(self) -> None:
        """Save text to file"""
        self.autosave_timer.stop()
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

    def cursor_word(self) -> str:
        """Cursor word"""
        c: QTextCursor = self.textCursor()
        c.select(QTextCursor.SelectionType.WordUnderCursor)
        return c.selection().toPlainText()

    def insert_completion(self, text: str) -> None:
        """Insert completion to text"""
        c: QTextCursor = self.textCursor()
        c.select(QTextCursor.SelectionType.WordUnderCursor)
        c.insertText(text)
        self.setTextCursor(c)

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
            if (fa := re.findall(r'\b\S+\b', txt_1)) and self.highlighter and fa[0] in self.highlighter.tab_words:
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
        elif e.key() == Qt.Key.Key_Alt and (self.completer is not None and self.pr_settings.value('Completer') and
                                            self.completer.completionPrefix()):
            self.completer.activated.emit(self.completer.currentCompletion())
            e.accept()
            self.completer.popup().hide()
            return
        else:
            QPlainTextEdit.keyPressEvent(self, e)

        if not self.completer or not self.toPlainText() or not self.pr_settings.value('Completer'):
            return
        self.completer.setCompletionPrefix(self.cursor_word())
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