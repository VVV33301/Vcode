from PyQt6.QtWidgets import QMenu, QTreeView, QApplication, QTabWidget
from PyQt6.QtGui import QAction, QKeySequence, QContextMenuEvent
from PyQt6.QtCore import QSettings, QMimeData, QUrl
import shutil
from os import mkdir, rename, remove, system
from os.path import isfile, isdir
import sys
import texts
from .inputdialog import InputDialog
from .warning import WarningMessageBox


class TreeViewMenu(QMenu):
    """Custom QTreeView Menu"""

    def __init__(self, parent: QTreeView, parent_class, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        self.p: QTreeView = parent
        self.c = parent_class

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
            pth: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0] if self.c.tree.selectedIndexes() \
                else self.c.tree.rootIndex())
            try:
                if file.text_value().endswith(('/', '\\')):
                    mkdir((pth if isdir(pth) else pth.rsplit('/', maxsplit=1)[0]) + '/' + file.text_value())
                else:
                    x: str = (pth if isdir(pth) else pth.rsplit('/', maxsplit=1)[0]) + '/' + file.text_value()
                    open(x, 'w', encoding=self.lang_s.value('Encoding')).close()
                    self.c.add_tab(x)
            except OSError:
                WarningMessageBox(self.c, texts.warning_text, texts.permission_denied).wait()

    def copy_file(self) -> None:
        """Copy file to clipboard"""
        md: QMimeData = QMimeData()
        ls: list[QUrl] = []
        for i in self.c.tree.selectedIndexes():
            ls.append(QUrl('file:///' + self.c.model.filePath(i)))
        md.setUrls(ls)
        QApplication.instance().clipboard().setMimeData(md)

    def paste_file(self) -> None:
        """Paste file from clipboard"""
        new_path: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0] if self.c.tree.selectedIndexes() \
                                              else self.c.tree.rootIndex())
        if isdir(new_path):
            try:
                for url in QApplication.instance().clipboard().mimeData().urls():
                    path: str = url.url().replace('file:///', '')
                    if isfile(path):
                        shutil.copy2(
                            path, new_path + '/' + QApplication.instance().clipboard().mimeData().urls()[0].fileName())
                    elif isdir(path):
                        shutil.copytree(path, new_path + '/' + path.rsplit('/', maxsplit=1)[-1])
            except OSError:
                WarningMessageBox(self.c, texts.warning_text, texts.permission_denied).wait()

    def delete_file(self) -> None:
        """Delete file"""
        n: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0])
        try:
            if isfile(n):
                remove(n)
            elif isdir(n):
                shutil.rmtree(n)
        except OSError:
            WarningMessageBox(self.c, texts.warning_text, texts.permission_denied).wait()

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
                for i in range(self.c.editor_tabs.count()):
                    x = self.c.editor_tabs.widget(i)
                    if x.file == path + '/' + name:
                        x.file = path + '/' + file.text_value()
                        x.filename = file.text_value()
                        self.c.editor_tabs.setTabText(i, file.text_value())
            except Exception:
                pass

    def open_in_explorer(self) -> None:
        """Open file or directory in explorer"""
        pth: str = self.c.model.filePath(self.c.tree.selectedIndexes()[0]).replace('/', '\\')
        if isfile(pth):
            pth = pth.rsplit('\\', maxsplit=1)[0]
        if sys.platform == 'win32':
            system(f'explorer "{pth}"')
        elif sys.platform == 'linux':
            system(f'xdg-open "{pth}"')
        elif sys.platform == 'darwin':
            system(f'open "{pth}"')
