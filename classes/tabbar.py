from PyQt6.QtWidgets import QMenu, QTabWidget
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtCore import Qt, QSettings, QPoint
import sys
from os import system
import texts


class TabBarMenu(QMenu):
    """Menu for tab bar"""

    def __init__(self, parent: QTabWidget, ide, *args, **kwargs) -> None:
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
