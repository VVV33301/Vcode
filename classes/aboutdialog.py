from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt
from webbrowser import open_new
from functions import resource_path
from ide import VERSION


class AboutDialog(QDialog):
    """Dialog about program"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setModal(True)
        self.setWindowTitle(f'Vcode v{VERSION}')
        self.setMinimumSize(250, 200)
        layout: QVBoxLayout = QVBoxLayout()
        self.setLayout(layout)

        self.icon: QLabel = QLabel(self)
        self.icon.setPixmap(QPixmap(resource_path('Vcode.ico')).scaled(128, 128))
        self.icon.resize(128, 128)
        layout.addWidget(self.icon, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.name: QLabel = QLabel('Vcode', self)
        self.name.setFont(QFont('Arial', 18))
        layout.addWidget(self.name, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.text: QLabel = QLabel(f'Version: {VERSION}<br><br><a href="https://vcodeide.ru">vcodeide.ru</a>'
                                   f'<br><br>Vladimir Varenik<br>'
                                   f'Copyright 2023-2024. All rights reserved<br>'
                                   f'This program is under GNU General Public License', self)
        self.text.setOpenExternalLinks(True)
        layout.addWidget(self.text)

        self.license: QPushButton = QPushButton('Read license', self)
        self.license.clicked.connect(lambda: open_new('file:///' + resource_path('LICENSE')))
        layout.addWidget(self.license)

        self.text2: QLabel = QLabel('This program powered by PyQt6', self)
        layout.addWidget(self.text2)
