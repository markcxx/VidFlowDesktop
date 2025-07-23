# coding:utf-8
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import MessageBoxBase, SubtitleLabel, PushButton, IndeterminateProgressRing


class CustomMessageBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None, title='正在解析,请稍等...'):
        super().__init__(parent)
        self.progressring = IndeterminateProgressRing(self)
        self.tip_label = SubtitleLabel(title, self)
        self.hboxLayout = QHBoxLayout()
        self.hboxLayout.setContentsMargins(0, 0, 0, 0)
        self.hboxLayout.setSpacing(20)
        self.hboxLayout.addWidget(self.progressring, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.hboxLayout.addWidget(self.tip_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # add widget to view layout
        self.viewLayout.addLayout(self.hboxLayout, 0)
        self.buttonGroup.hide()

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.autoClose)
        self.timer.start(7000)

    def autoClose(self):
        self.reject()


class Demo(QWidget):

    def __init__(self):
        super().__init__()
        # setTheme(Theme.DARK)
        # self.setStyleSheet('Demo{background:rgb(32,32,32)}')

        self.hBxoLayout = QHBoxLayout(self)
        self.button = PushButton('打开 URL', self)

        self.resize(600, 600)
        self.hBxoLayout.addWidget(self.button, 0, Qt.AlignCenter)
        self.button.clicked.connect(self.showDialog)

    def showDialog(self):
        w = CustomMessageBox(self)
        w.show()


if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec_()