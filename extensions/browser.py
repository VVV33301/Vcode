from PyQt6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QToolBar, QWidgetAction
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import QUrl, pyqtSlot, QCoreApplication, Qt

QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage
except ImportError:
    import pip
    pip.main(['install', 'PyQt6-WebEngine'])
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage


class WebEnginePage(QWebEnginePage):
    def createWindow(self, _type):
        page = WebEnginePage(self)
        page.urlChanged.connect(self.on_url_changed)
        return page

    @pyqtSlot(QUrl)
    def on_url_changed(self, url):
        page = self.sender()
        self.setUrl(url)
        page.deleteLater()


class Browser(QMainWindow):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.setStyleSheet('QPushButton {width: 20px}')

        self.web = QWebEngineView(self)
        self.page = WebEnginePage(self)
        self.web.setPage(self.page)
        self.page.urlChanged.connect(self.update_urlbar)
        self.setCentralWidget(self.web)

        navtb = QToolBar(self)
        navtb.setMovable(False)
        self.addToolBar(navtb)

        back_btn = QWidgetAction(navtb)  # Кнопка передвижения на предыдущую страницу
        back_t = QPushButton(chr(10094))
        back_t.clicked.connect(lambda: self.web.back())
        back_btn.setDefaultWidget(back_t)
        back_btn.setShortcut(QKeySequence.StandardKey.Back)  # Горячая клавиша
        back_btn.triggered.connect(lambda: self.web.back())
        navtb.addAction(back_btn)

        next_btn = QWidgetAction(navtb)  # Кнопка передвижения на следующую страницу
        next_t = QPushButton(chr(10095))
        next_t.clicked.connect(lambda: self.web.forward())
        next_btn.setDefaultWidget(next_t)
        next_btn.setShortcut(QKeySequence.StandardKey.Forward)
        next_btn.triggered.connect(lambda: self.web.forward())
        navtb.addAction(next_btn)

        reload_btn = QWidgetAction(navtb)  # Кнопка обновления страницы
        reload_t = QPushButton(chr(11118))
        reload_t.clicked.connect(lambda: self.web.reload())
        reload_btn.setDefaultWidget(reload_t)
        reload_btn.setShortcut(QKeySequence.StandardKey.Refresh)
        reload_btn.triggered.connect(lambda: self.web.reload())
        navtb.addAction(reload_btn)

        stop_btn = QWidgetAction(navtb)  # Кнопка отмены обновления страницы
        stop_t = QPushButton(chr(10805))
        stop_t.clicked.connect(lambda: self.web.stop())
        stop_btn.setDefaultWidget(stop_t)
        stop_btn.setShortcut(QKeySequence.StandardKey.Cancel)
        stop_btn.triggered.connect(lambda: self.web.stop())
        navtb.addAction(stop_btn)

        home_btn = QWidgetAction(navtb)  # Кнопка возвращения на домашнюю страницу
        home_t = QPushButton(chr(8962))
        home_t.clicked.connect(self.go_home)
        home_btn.setDefaultWidget(home_t)
        home_btn.setShortcut('Home')
        home_btn.triggered.connect(self.go_home)
        navtb.addAction(home_btn)

        navtb.addSeparator()
        self.urlbar = QLineEdit()  # Строка с url страницы
        self.urlbar.returnPressed.connect(self.open_url)
        self.urlbar.setClearButtonEnabled(True)
        navtb.addWidget(self.urlbar)
        navtb.addSeparator()

        out_btn = QWidgetAction(navtb)  # Кнопка возвращения на домашнюю страницу
        out_t = QPushButton('X')
        out_t.clicked.connect(self.go_out)
        out_btn.setDefaultWidget(out_t)
        out_btn.setShortcut('Insert')
        out_btn.triggered.connect(self.go_out)
        navtb.addAction(out_btn)

        self.page.load(QUrl('https://ya.ru'))

    def update_urlbar(self):
        self.urlbar.setText(self.page.url().url())

    def open_url(self):
        if self.urlbar.text():
            if not self.urlbar.text().startswith('http'):
                self.urlbar.setText('http://' + self.urlbar.text())
            self.page.load(QUrl(self.urlbar.text()))
        else:
            self.page.load(QUrl('https://ya.ru'))

    def go_home(self):
        self.urlbar.setText('https://ya.ru')
        self.open_url()

    def go_out(self):
        self.parent.splitter.setSizes([self.parent.splitter.sizes()[0], sum(self.parent.splitter.sizes()[1:]), 0])


def main(ide):
    ide.browser = Browser(ide)
    ide.splitter.addWidget(ide.browser)
