from PyQt6.QtWidgets import QDialog, QLineEdit


class CreateProjectDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.path = QLineEdit(self)
        self.path.setPlaceholderText('Project path')
