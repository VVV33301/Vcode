from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout, QToolBar, QTreeView, QComboBox
from PyQt6.QtGui import QAction, QFileSystemModel
from PyQt6.QtCore import QSettings
from .inputdialog import InputDialog
import texts

try:
    import git
    GIT_INSTALLED: bool = True
except ImportError:
    git = None
    GIT_INSTALLED: bool = False


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