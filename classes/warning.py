from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import Qt, QSettings
import texts


class WarningMessageBox(QMessageBox):
    """Custom QMessageBox"""
    INFO: int = 0
    SAVE: int = 1
    UPDATE: int = 2

    def __init__(self, parent: QWidget, title: str, text_all_lang: dict[str, str],
                 msg_type: int = INFO) -> None:
        super().__init__(parent=parent)
        lang: str = QSettings('Vcode', 'Settings').value('Language')
        self.setWindowTitle(title)
        self.setText(text_all_lang[lang])

        if msg_type == self.SAVE:
            self.setStandardButtons(self.StandardButton.Save | self.StandardButton.Discard | self.StandardButton.Cancel)
            self.setDefaultButton(self.StandardButton.Save)
            self.button(self.StandardButton.Save).setText(texts.save_btn[lang])
            self.button(self.StandardButton.Discard).setText(texts.discard_btn[lang])
            self.button(self.StandardButton.Cancel).setText(texts.cancel_btn[lang])
        elif msg_type == self.UPDATE:
            self.setStandardButtons(self.StandardButton.Yes | self.StandardButton.No)
            self.setDefaultButton(self.StandardButton.Yes)
            self.button(self.StandardButton.Yes).setText(texts.update_btn[lang])
            self.button(self.StandardButton.No).setText(texts.cancel_btn[lang])
        else:
            self.setStandardButtons(self.StandardButton.Ok)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def wait(self) -> str:
        """Start GUI, wait exit and return clicked button"""
        self.exec()
        return self.clickedButton().text()
