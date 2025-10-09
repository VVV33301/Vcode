from PyQt6.QtWidgets import QTextEdit, QPlainTextEdit, QMenu
from PyQt6.QtGui import QAction, QContextMenuEvent, QActionGroup, QFont
from .texteditwindow import TextEditWindowMenu
import texts


class TextEditFullscreenMenu(TextEditWindowMenu):
    """TextEditMenu for presentation mode"""

    def __init__(self, parent: QTextEdit | QPlainTextEdit, ide, *args, **kwargs) -> None:
        super().__init__(parent=parent, ide=ide, *args, **kwargs)

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
