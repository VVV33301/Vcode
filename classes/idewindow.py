from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QTreeView, QRadioButton, QToolBar, QLabel, QSizePolicy,
                             QMenu, QSplitter, QFileDialog, QTabWidget, QListWidgetItem)
from PyQt6.QtGui import (QFileSystemModel, QAction, QKeySequence, QFont, QFontDatabase, QTextCursor, QDragEnterEvent,
                         QDropEvent, QCloseEvent)
from PyQt6.QtCore import Qt, QSettings, QDir, QItemSelectionModel, QMimeData
from requests import get
import threading
import subprocess
from webbrowser import open as openweb
from os import remove, system, execv
from os.path import isdir, isfile, exists
import json
import texts
from functions import *
from .aboutdialog import AboutDialog
from .editortab import EditorTab
from .extensionssettings import ExtensionsSettings
from .findwindow import FindWindow
from .git import git, GIT_INSTALLED
from .highlighter import Highlighter
from .highlightmaker import HighlightMaker
from .inputdialog import InputDialog
from .projectsettingsdialog import ProjectSettingsDialog
from .settingsdialog import SettingsDialog
from .systemmonitor import SystemMonitor
from .tabwidget import TabWidget
from .textedit import TextEditMenu
from .texteditfullscreen import TextEditFullscreenMenu
from .texteditwindow import TextEditWindowMenu
from .treeview import TreeViewMenu
from .warning import WarningMessageBox
from default import USER, CONFIG_PATH, LANGUAGES
from ide import VERSION, style, language_list
import extensions


class IdeWindow(QMainWindow):
    """Main app window"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Vcode')
        self.setMinimumSize(300, 200)
        self.resize(1000, 700)
        self.setAcceptDrops(True)

        self.settings: QSettings = QSettings('Vcode', 'Settings')
        self.options: QSettings = QSettings('Vcode', 'Options')
        self.history: QSettings = QSettings('Vcode', 'History')
        self.ext_list: QSettings = QSettings('Vcode', 'Extensions')

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

        self.extensions: QTabWidget = QTabWidget(self)
        self.extensions.setTabPosition(QTabWidget.TabPosition.East)
        self.extensions.setMovable(True)
        self.extensions.setMinimumWidth(20)

        self.splitter: QSplitter = QSplitter()
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.editor_tabs)
        self.splitter.addWidget(self.extensions)
        self.splitter.setCollapsible(1, False)
        self.splitter.setCollapsible(2, False)
        self.setCentralWidget(self.splitter)

        self.ext_enabled: ExtensionsSettings = ExtensionsSettings(self)
        self.ext_enabled.list.itemClicked.connect(self.extension_enable)

        self.tool_bar: QToolBar = QToolBar(self)
        self.tool_bar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.tool_bar)
        self.tool_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.menuBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

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

        self.ext_list_btn: QAction = QAction(self)
        self.ext_list_btn.setShortcut('Ctrl+Shift+X')
        self.ext_list_btn.triggered.connect(self.ext_enabled.exec)
        self.view_menu.addAction(self.ext_list_btn)

        self.settings_btn: QAction = QAction(self)
        self.settings_btn.triggered.connect(self.settings_window.exec)
        self.menuBar().addAction(self.settings_btn)

        self.proj_menu: QMenu = QMenu(self)
        self.menuBar().addMenu(self.proj_menu)

        self.new_proj_btn: QAction = QAction(self)
        self.new_proj_btn.triggered.connect(self.new_project)
        self.proj_menu.addAction(self.new_proj_btn)

        self.open_proj_btn: QAction = QAction(self)
        self.open_proj_btn.triggered.connect(self.open_project)
        self.proj_menu.addAction(self.open_proj_btn)

        self.save_proj_btn: QAction = QAction(self)
        self.save_proj_btn.triggered.connect(self.save_project)
        self.proj_menu.addAction(self.save_proj_btn)

        self.close_proj_btn: QAction = QAction(self)
        self.close_proj_btn.triggered.connect(self.close_project)
        self.proj_menu.addAction(self.close_proj_btn)

        self.proj_menu.addSeparator()

        self.settings_proj_btn: QAction = QAction(self)
        self.settings_proj_btn.triggered.connect(self.project_settings)
        self.proj_menu.addAction(self.settings_proj_btn)

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

        self.branch: QAction = QAction('Branch', self)
        self.branch.triggered.connect(self.git_change_branch)
        self.git_menu.addAction(self.branch)

        self.commit: QAction = QAction('Commit', self)
        self.commit.triggered.connect(self.git_commit)
        self.git_menu.addAction(self.commit)

        self.push: QAction = QAction('Push', self)
        self.push.triggered.connect(self.git_push)
        self.git_menu.addAction(self.push)

        self.merge: QAction = QAction('Merge', self)
        self.merge.triggered.connect(self.git_merge)
        self.git_menu.addAction(self.merge)

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

        if self.settings.value('Autorun') is None:
            self.settings.setValue('Autorun', 0)
        if self.settings.value('Autosave') is None:
            self.settings.setValue('Autosave', 0)
        if self.settings.value('Recent') is None:
            self.settings.setValue('Recent', 1)
        if self.settings.value('Completer') is None:
            self.settings.setValue('Completer', 1)
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

        self.select_style(self.settings.value('Style'))

        if not self.options.allKeys():
            self.options.setValue('Splitter', [215, 775, 10])
            self.options.setValue('Folder', USER)
            self.options.setValue('Geometry', 'Not init')
        self.splitter.setSizes(map(int, self.options.value('Splitter')))

        self.settings_window.language.setCurrentText(
            next(filter(lambda lg: lg[1] == self.settings.value('Language'), LANGUAGES.items()))[0])
        self.settings_window.language.currentTextChanged.connect(
            lambda: self.select_language(LANGUAGES[self.settings_window.language.currentText()]))

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

        self.settings_window.completer.setChecked(bool(self.settings.value('Completer')))
        self.settings_window.completer.stateChanged.connect(
            lambda: self.settings.setValue('Completer', int(self.settings_window.completer.isChecked())))

        self.settings_window.tab_size.setValue(int(self.settings.value('Tab size')))
        self.settings_window.tab_size.valueChanged.connect(
            lambda: self.settings.setValue('Tab size', self.settings_window.tab_size.value()))

        self.settings_window.fonts.setCurrentText(self.settings.value('Font').family())
        self.settings_window.fonts.currentTextChanged.connect(self.select_font)

        self.settings_window.font_size.setValue(self.settings.value('Font').pointSize())
        self.settings_window.font_size.valueChanged.connect(self.select_font)

        self.project: dict[str, str] | None = None
        self.git_repo: git.Repo | None = None

        for ext in extensions.mains.keys():
            if self.ext_list.value(ext, None) is None:
                self.ext_list.setValue(ext, 1)
            if self.ext_list.value(ext):
                extensions.mains[ext](ide=self)
            ei: QListWidgetItem = QListWidgetItem(self.ext_enabled.list)
            ei.setText(ext)
            ei.setFlags(ei.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            ei.setCheckState(Qt.CheckState.Checked if self.ext_list.value(ext) else Qt.CheckState.Unchecked)

        self.select_language(self.settings.value('Language'))
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
        threading.Thread(target=check, daemon=True).start()

    def show_monitor(self) -> None:
        """Run system monitor"""
        SystemMonitor(self).show()

    def sel_tab(self) -> None:
        """Change current tab"""
        if self.editor_tabs.count():
            self.setWindowTitle(self.editor_tabs.currentWidget().windowTitle() +
                                (' - ' + self.project['name'] if self.project else '') + ' - Vcode')
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
            self.setWindowTitle(((self.project['name'] + ' - ') if self.project else '') + 'Vcode')
            self.position_code.setText('')
            self.selection_code.setText('')
            self.edit_menu.setEnabled(False)

    def add_tab(self, filename: str, row: int | None = None) -> None:
        """Add new text tab"""
        if not isfile(filename):
            return
        filename = filename.replace('\\', '/')
        for tab in self.editor_tabs.findChildren(EditorTab):
            if tab.file == filename:
                self.editor_tabs.setCurrentWidget(tab)
                return
        if filename.endswith('.hl'):
            hmt: HighlightMaker = HighlightMaker(filename)
            hmt.setWindowTitle(f'{filename.split("/")[-1]} - Vcode highlight maker')
            hmt.exec()
            return
        if filename.endswith('.vcodeproject'):
            if self.project is None:
                self.open_project(filename.replace('/.vcodeproject', ''))
            vprs: ProjectSettingsDialog = ProjectSettingsDialog(self.project, self)
            vprs.exec()
            return
        editor: EditorTab = EditorTab(filename, self)
        editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        editor.textChanged.connect(self.auto_save)
        editor.setFont(self.settings.value('Font'))
        editor.contextMenuEvent = TextEditMenu(editor, self)
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
        if self.project:
            if self.project['highlight']:
                editor.set_highlighter(Highlighter(resource_path(self.project['highlight'])))
            editor.start_command = self.project['start_command']
            editor.debug_command = self.project['debug_command']
        else:
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

    def close_tab(self, tab: int) -> None:
        """Close tab"""
        widget: EditorTab = self.editor_tabs.widget(tab)
        if type(widget) is EditorTab:
            if widget.saved_text != widget.toPlainText():
                button_text: str = WarningMessageBox(self, texts.warning_text,
                                                     texts.save_warning, WarningMessageBox.SAVE).wait()
                if button_text in texts.cancel_btn.values():
                    return
                elif button_text in texts.save_btn.values():
                    widget.save()
        widget.deleteLater()
        self.editor_tabs.removeTab(tab)

    def close_all_tabs(self) -> None:
        """Close all tabs"""
        for tab in range(self.editor_tabs.count()):
            self.close_tab(0)

    def new_project(self, *, dirpath: str | None = None) -> None:
        """Create a new project"""
        if dirpath is None:
            dirpath: str = QFileDialog.getExistingDirectory(directory=self.options.value('Folder')).replace('\\', '/')
            if not dirpath:
                return
        self.project = {"path": dirpath, "name": dirpath.split('/')[-1], "highlight": "", "start_command": "",
                        "debug_command": "", "git": 'false'}
        if GIT_INSTALLED and git.Repo(dirpath).git_dir:
            self.project['git'] = 'true'
        with open(dirpath + '/.vcodeproject', 'w') as vcodeproject:
            json.dump(self.project, vcodeproject)
        self.open_project(dirpath)

    def open_project(self, proj: str | None = None) -> None:
        """Open project in the editor"""
        if proj is None:
            proj: str = QFileDialog.getExistingDirectory(directory=self.options.value('Folder')).replace('\\', '/')
        if proj and isdir(proj):
            self.options.setValue('Folder', proj)
            if not exists(proj + '/.vcodeproject'):
                self.new_project(dirpath=proj)
                return
            with open(proj + '/.vcodeproject') as vcodeproject:
                self.project = json.load(vcodeproject)
            if self.project['git'] == 'true':
                self.git_repo = git.Repo(proj)
            self.tree.setRootIndex(self.model.index(proj))
            self.close_all_tabs()
            self.sel_tab()

    def save_project(self) -> None:
        """Save project in the editor"""
        for edt in self.editor_tabs.findChildren(EditorTab):
            edt.save()

    def close_project(self) -> None:
        """Close project in the editor"""
        self.project = None
        self.git_repo = None
        self.tree.setRootIndex(self.model.index(''))
        self.close_all_tabs()
        self.sel_tab()

    def project_settings(self) -> None:
        if self.project:
            prs: ProjectSettingsDialog = ProjectSettingsDialog(self.project, self)
            prs.exec()

    def new_window(self, tab: int) -> None:
        """Show current tab in new window"""
        t: EditorTab | QWidget = self.editor_tabs.widget(tab)
        if type(t) is EditorTab:
            self.editor_tabs.removeTab(tab)
            t.contextMenuEvent = TextEditWindowMenu(t, self)
            t.closeEvent = lambda e, x=t: self.close_window(e, x)
            t.setParent(None, Qt.WindowType.Window)
            t.show()

    def presentation_mode(self) -> None:
        """Show current tab fullscreen"""
        t: EditorTab | QWidget = self.editor_tabs.currentWidget()
        if type(t) is not EditorTab:
            return
        self.editor_tabs.removeTab(self.editor_tabs.currentIndex())
        t.contextMenuEvent = TextEditFullscreenMenu(t, self)
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

    def close_window_mode(self, t: EditorTab) -> None:
        """Return windowed tab to tab widget"""
        t.showNormal()
        t.closeEvent = EditorTab.closeEvent
        t.setWindowFlag(Qt.WindowType.Widget)
        if type(t) is EditorTab:
            t.setFont(self.settings.value('Font'))
            t.contextMenuEvent = TextEditMenu(t, self)
            self.editor_tabs.setCurrentIndex(self.editor_tabs.addTab(t, t.filename))
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
        self.proj_menu.setTitle(texts.proj_menu[language])
        self.new_proj_btn.setText(texts.new_proj_btn[language])
        self.open_proj_btn.setText(texts.open_proj_btn[language])
        self.save_proj_btn.setText(texts.save_proj_btn[language])
        self.close_proj_btn.setText(texts.close_proj_btn[language])
        self.settings_proj_btn.setText(texts.settings_btn[language])
        self.about_menu.setTitle(texts.about_menu[language])
        self.about_btn.setText(texts.about_btn[language])
        self.feedback_btn.setText(texts.feedback_btn[language])
        self.check_updates_btn.setText(texts.check_btn[language])
        self.download_btn.setText(texts.download_btn[language])
        self.view_menu.setTitle(texts.view_btn[language])
        self.monitor_btn.setText(texts.monitor_btn[language])
        self.presentation_btn.setText(texts.presentation_btn[language])
        self.ext_list_btn.setText(texts.extensions_btn[language])
        self.edit_menu.setTitle(texts.edit_btn[language])
        self.undo.setText(texts.undo[language])
        self.redo.setText(texts.redo[language])
        self.cut.setText(texts.cut[language])
        self.copy.setText(texts.copy[language])
        self.paste.setText(texts.paste[language])
        self.select_all.setText(texts.select_all[language])
        self.find_btn.setText(texts.find_btn[language])

        self.ext_enabled.setWindowTitle(texts.extensions_btn[language])
        self.ext_enabled.import_btn.setText(texts.import_btn[language])

        self.settings_window.autorun.setText(texts.autorun[language])
        self.settings_window.autosave.setText(texts.autosave[language])
        self.settings_window.recent.setText(texts.recent[language])
        self.settings_window.completer.setText(texts.completer[language])
        self.settings_window.tab_size.setPrefix(texts.tab_size[language])
        self.settings_window.style_select_group.setTitle(texts.style_select_group[language])
        self.settings_window.font_select_group.setTitle(texts.font_select_group[language])

        for obj in range(self.extensions.count()):
            if hasattr(self.extensions.widget(obj), 'select_language'):
                self.extensions.widget(obj).select_language(language)

    def select_style(self, style_name: str) -> None:
        """Set style to windows"""
        if style_name in style.keys():
            self.settings.setValue('Style', style_name)
            QApplication.instance().setStyleSheet(style[style_name])

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
        file_ed = self.editor_tabs.currentWidget()
        if file_ed is None or type(file_ed) is not EditorTab:
            folder = USER
        else:
            folder = file_ed.path
        if sys.platform == 'win32':
            system(f'cd {folder} && start "Vcode terminal" powershell')
        elif sys.platform.startswith('linux'):
            system('bash')
        else:
            self.exit_code.setText('Can`t start terminal in this operating system')

    def start_program(self, file_ed: EditorTab = None) -> None:
        """Run code"""
        if file_ed is None or type(file_ed) is not EditorTab:
            file_ed = self.editor_tabs.currentWidget()
            if file_ed is None or type(file_ed) is not EditorTab:
                return
        if not self.settings.value('Autosave') and file_ed.saved_text != file_ed.toPlainText():
            button_text: str = WarningMessageBox(self, texts.warning_text, texts.save_warning,
                                                 WarningMessageBox.SAVE).wait()
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
            button_text: str = WarningMessageBox(self, texts.warning_text, texts.save_warning,
                                                 WarningMessageBox.SAVE).wait()
            if button_text in texts.cancel_btn.values():
                return
            elif button_text in texts.save_btn.values():
                file_ed.save()
        self.show_monitor()
        threading.Thread(target=self.program, args=[file_ed, True]).start()

    def program(self, code: EditorTab, debug: bool = False) -> None:
        """Code working process"""
        pth: str = code.path
        fnm: str = code.filename
        if self.project:
            tid: str = str(threading.current_thread().native_id)
            command: str = self.project['start_command'] if not debug else self.project['debug_command']
        elif code.language in language_list.keys():
            tid: str = str(threading.current_thread().native_id)
            command: str = code.start_command if not debug else code.debug_command
        else:
            self.exit_code.setText(f'Can`t start "{fnm}"')
            return
        if sys.platform == 'win32':
            with open(f'{CONFIG_PATH}/process_{tid}.bat', 'w', encoding='utf-8') as bat_win32:
                bat_win32.write(f'@echo off\nchcp 65001>nul\ncd {pth}\necho Interrupted > {fnm}.output\n'
                                f'{command.format(filename=fnm)}\necho Exit code: %errorlevel%\n'
                                f'echo %errorlevel% > {fnm}.output\npause')
            process: subprocess.Popen = subprocess.Popen(f'{CONFIG_PATH}/process_{tid}.bat',
                                                         creationflags=subprocess.CREATE_NEW_CONSOLE,
                                                         process_group=subprocess.CREATE_NEW_PROCESS_GROUP)
            process.wait()
            remove(f'{CONFIG_PATH}/process_{tid}.bat')
        elif sys.platform.startswith('linux'):
            with open(f'{CONFIG_PATH}/process_{tid}.sh', 'w', encoding='utf-8') as bat_linux:
                bat_linux.write(f'#!/bin/bash\ncd {pth}\necho "Interrupted" > {fnm}.output\n'
                                f'{command.format(filename=fnm)}\nec=$?\necho "Exit code: $ec"\n'
                                f'echo $ec > {fnm}.output\nread -r -p "Press enter to continue..." key')
            system(f'chmod +x {resource_path(f"{CONFIG_PATH}/process_{tid}.sh")}')
            process: subprocess.Popen = subprocess.Popen(resource_path(f"{CONFIG_PATH}/process_{tid}.sh"), shell=True)
            process.wait()
            remove(f'{CONFIG_PATH}/process_{tid}.sh')
        else:
            with open(f'{pth}/{fnm}.output', 'w') as bat_w:
                bat_w.write('Can`t start terminal in this operating system')
        with open(f'{pth}/{fnm}.output') as bat_output:
            if len(x := bat_output.readlines()) == 1:
                self.exit_code.setText(f'Exit code: {x[0].rstrip()}')
            else:
                self.exit_code.setText('Interrupted')
        remove(f'{pth}/{fnm}.output')

    def save_file(self) -> None:
        """Save text to file"""
        if self.editor_tabs.count():
            self.editor_tabs.currentWidget().save()

    def new_file(self) -> None:
        """Create new file"""
        file: str = QFileDialog.getSaveFileName(directory=self.options.value('Folder') + '/untitled',
                                                filter=';;'.join(update_filters(language_list)))[0]
        if file:
            self.options.setValue('Folder', file.rsplit('/', maxsplit=1)[0])
            open(file, 'w', encoding=self.settings.value('Encoding')).close()
            self.add_tab(file)

    def open_file(self) -> None:
        """Open file"""
        file: str = QFileDialog.getOpenFileName(directory=self.options.value('Folder'),
                                                filter=';;'.join(update_filters(language_list)))[0]
        if file:
            self.options.setValue('Folder', file.rsplit('/', maxsplit=1)[0])
            self.add_tab(file)

    def save_as(self) -> None:
        """Save file as new file"""
        if self.editor_tabs.count():
            path, _ = QFileDialog.getSaveFileName(
                directory=self.options.value('Folder') + '/' + self.editor_tabs.currentWidget().filename,
                filter=';;'.join(update_filters(language_list)))
            if path:
                self.options.setValue('Folder', path.rsplit('/', maxsplit=1)[0])
                with open(path, 'w') as sf:
                    sf.write(self.editor_tabs.currentWidget().toPlainText())
                self.add_tab(path)

    def auto_save(self) -> None:
        """Save file when text changes"""
        if self.settings.value('Autosave'):
            self.editor_tabs.currentWidget().saved_text = self.editor_tabs.currentWidget().toPlainText()
            self.editor_tabs.currentWidget().autosave_timer.start(1000)

    def git_open(self) -> None:
        """Open git repository on computer"""
        if GIT_INSTALLED:
            path: str = QFileDialog.getExistingDirectory(directory=USER)
            if path:
                try:
                    if git.Repo(path).git_dir:
                        self.open_project(path)
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
                self.open_project(path)
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

    def git_change_branch(self) -> None:
        """Change current branch"""
        if GIT_INSTALLED and self.git_repo:
            branch: InputDialog = InputDialog('Branch', 'Branch', self)
            branch.exec()
            if branch.text_value():
                self.git_repo.head.set_reference(branch.text_value())
                self.git_repo.head.reset(working_tree=True)

    def git_merge(self) -> None:
        """Merge from other commits"""
        if GIT_INSTALLED and self.git_repo:
            self.git_repo.merge_base()

    def git_commit(self) -> None:
        """Create new commit"""
        if GIT_INSTALLED and self.git_repo:
            git_descr: InputDialog = InputDialog('Commit', 'Commit description', self)
            git_descr.exec()
            if git_descr.text_value():
                for i in self.tree.selectedIndexes():
                    self.git_repo.index.add(self.model.filePath(i))
                self.git_repo.index.commit(git_descr.text_value())

    def git_push(self) -> None:
        """Push commits"""
        if GIT_INSTALLED and self.git_repo:
            self.git_repo.remotes.origin.push()

    def extension_enable(self, item: QListWidgetItem) -> None:
        """Set enabled extension"""
        if item.checkState() == Qt.CheckState.Unchecked and self.ext_list.value(item.text()) == 1:
            self.ext_list.setValue(item.text(), 0)
            self.restart()
        elif item.checkState() == Qt.CheckState.Checked and self.ext_list.value(item.text()) == 0:
            self.ext_list.setValue(item.text(), 1)
            self.restart()

    def restart(self) -> None:
        """Restart the program"""
        if (WarningMessageBox(self, texts.restart_btn, texts.restart_warning, WarningMessageBox.RESTART).wait() ==
                texts.restart_btn[self.settings.value('Language')]):
            self.close()
            execv(sys.executable, [sys.executable] + sys.argv)
            exit()

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
        for wgt in QApplication.instance().allWidgets():
            if type(wgt) is EditorTab and wgt.saved_text != wgt.toPlainText():
                button_text: str = WarningMessageBox(self, texts.warning_text, texts.save_warning,
                                                     WarningMessageBox.SAVE).wait()
                if button_text in texts.cancel_btn.values():
                    a0.ignore()
                    return
                elif button_text in texts.save_btn.values():
                    for stab in QApplication.instance().findChildren(EditorTab):
                        stab.save()
                    a0.accept()
                else:
                    a0.accept()
                break
        save_last: QSettings = QSettings('Vcode', 'Last')
        for tab in filter(lambda w: type(w) is EditorTab, QApplication.instance().allWidgets()):
            if self.editor_tabs.indexOf(tab) == -1:
                tab.close()
            save_last.setValue(tab.file, self.editor_tabs.indexOf(tab))
        save_last.setValue('current', self.editor_tabs.currentIndex())
        if self.project:
            save_last.setValue('project', self.project['path'])
        self.options.setValue('Splitter', self.splitter.sizes())
        if self.isMaximized():
            self.options.setValue('Geometry', 'Maximized')
        else:
            self.options.setValue('Geometry', self.geometry())
