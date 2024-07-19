from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QHBoxLayout, QComboBox, QSpinBox, QWidget, QCheckBox,
                             QListWidget, QListWidgetItem, QGridLayout, QMenu, QMainWindow)
from PyQt6.QtGui import QAction, QFontDatabase, QContextMenuEvent
from PyQt6.QtCore import QSettings
import json
from default import *
from .inputdialog import InputDialog
from .languagesettingsdialog import LanguageSettingsDialog
from .warning import WarningMessageBox
from ide import language_list
import texts


class SettingsDialog(QDialog):
    """Settings window"""

    def __init__(self, parent: QMainWindow, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.setModal(True)
        self.parent: QMainWindow = parent
        self.lang: str = QSettings('Vcode', 'Settings').value('Language')

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
        self.language.addItems(LANGUAGES.keys())
        self.check_boxes_layout.addWidget(self.language)

        self.autorun: QCheckBox = QCheckBox(self)
        self.check_boxes_layout.addWidget(self.autorun)

        self.autosave: QCheckBox = QCheckBox(self)
        self.check_boxes_layout.addWidget(self.autosave)

        self.recent: QCheckBox = QCheckBox(self)
        self.check_boxes_layout.addWidget(self.recent)

        self.completer: QCheckBox = QCheckBox(self)
        self.check_boxes_layout.addWidget(self.completer)

        self.tab_size: QSpinBox = QSpinBox(self)
        self.tab_size.setMinimum(1)
        self.tab_size.setMaximum(16)
        self.font_select_layout.addWidget(self.tab_size)

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

        self.reset_btn: QAction = QAction(self)
        self.reset_btn.triggered.connect(self.reset_languages)

    def language_settings(self) -> None:
        """Open settings of language"""
        lsd: LanguageSettingsDialog = LanguageSettingsDialog(
            self.languages_list.currentItem().text(), self.parent, self)
        lsd.setWindowTitle(f'{self.languages_list.currentItem().text()} - Vcode languages')
        lsd.exec()

    def languages_context_menu(self, event: QContextMenuEvent) -> None:
        """Custom context menu for language list"""
        menu: QMenu = QMenu(self)
        item: QListWidgetItem = self.languages_list.itemAt(event.pos())
        if item:
            self.remove_btn.setText(texts.remove_btn[self.lang])
            menu.addAction(self.remove_btn)
            if item.text() in ['Python', 'Html', 'JSON', 'PHP']:
                menu.setEnabled(False)
        else:
            self.add_btn.setText(texts.add_btn[self.lang])
            menu.addAction(self.add_btn)
            self.reset_btn.setText(texts.reset_btn[self.lang])
            menu.addAction(self.reset_btn)
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

    def reset_languages(self) -> None:
        """Reset all languages"""
        language_list: dict[str, dict[str, str]] = {"Python": python_ll, "Html": html_ll, "JSON": json_ll,
                                                    "PHP": php_ll}
        with open(USER + '/.Vcode/languages.json', 'w') as llf:
            json.dump(language_list, llf)
        with open(USER + '/.Vcode/highlights/python.hl', 'w') as llf:
            llf.write(python_hl)
        with open(USER + '/.Vcode/highlights/html.hl', 'w') as llf:
            llf.write(html_hl)
        with open(USER + '/.Vcode/highlights/json.hl', 'w') as llf:
            llf.write(json_hl)
        with open(USER + '/.Vcode/highlights/php.hl', 'w') as llf:
            llf.write(php_hl)
        rst: str = WarningMessageBox(self, 'Reset', texts.restart_warning, WarningMessageBox.RESTART).wait()
        if rst == texts.restart_btn[self.lang]:
            self.parent.restart()
