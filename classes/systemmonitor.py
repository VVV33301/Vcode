from PyQt6.QtWidgets import QDialog, QProgressBar, QVBoxLayout
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtCore import QTimer
import psutil
from os import getpid


class SystemMonitor(QDialog):
    """Show CPU percent and memory usage"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Vcode System monitor')
        self.setMinimumSize(300, 200)
        self.lay: QVBoxLayout = QVBoxLayout(self)
        self.setLayout(self.lay)

        self.ide_process: psutil.Process = psutil.Process(getpid())
        self.list_processes: list[psutil.Process] = []

        self.processor: QProgressBar = QProgressBar(self)
        self.processor.setObjectName('monitor')
        self.processor.setFormat('CPU usage: %p%')
        self.lay.addWidget(self.processor)

        self.ram: QProgressBar = QProgressBar(self)
        self.ram.setObjectName('monitor')
        self.ram.setFormat('Memory usage: %p% - %v MB')
        self.ram.setMaximum(self.bytes_to_mb(psutil.virtual_memory().total))
        self.lay.addWidget(self.ram)

        self.ide: QProgressBar = QProgressBar(self)
        self.ide.setObjectName('monitor')
        self.ide.setFormat('Vcode memory usage: %p% - %v MB')
        self.ide.setMaximum(self.bytes_to_mb(psutil.virtual_memory().total))
        self.lay.addWidget(self.ide)

        self.monitor()

        self.timer: QTimer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.monitor)
        self.timer.start()

    def monitor(self) -> None:
        """Update values"""
        self.processor.setValue(int(psutil.cpu_percent()))
        self.ram.setValue(self.bytes_to_mb(psutil.virtual_memory().used))
        self.ide.setValue(self.bytes_to_mb(self.ide_process.memory_info().rss))

    @staticmethod
    def bytes_to_mb(a: int | float) -> int:
        """Convert bytes to megabytes"""
        return int(a / 1024 / 1024)

    def closeEvent(self, a0: QCloseEvent) -> None:
        """Stop updating monitor"""
        self.timer.stop()
