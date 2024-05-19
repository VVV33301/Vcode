from PyQt6.QtWidgets import QMenu, QTextEdit, QPlainTextEdit
from PyQt6.QtGui import QAction, QKeySequence, QContextMenuEvent
from PyQt6.QtCore import QSettings
from webbrowser import open as openweb
from classes.findwindow import FindWindow
import texts


class TextEditMenu(QMenu):
    """Custom QTextEdit Menu"""

    def __init__(self, parent: QTextEdit | QPlainTextEdit, ide, *args, **kwargs) -> None:
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
