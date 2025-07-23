# coding:utf-8
import os
import sys
from inspect import getsourcefile
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme

os.chdir(Path(getsourcefile(lambda: 0)).resolve().parent)

from app.common.application import SingletonApplication
from app.view.main_window import MainWindow
from app.common.config import config

# enable dpi scale
if config.get(config.dpiScale) == "Auto":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
else:
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(config.get(config.dpiScale))

QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
app = SingletonApplication(sys.argv, "VidFlowDesktop")
# app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
w = MainWindow()
# setTheme(Theme.DARK)
w.show()

app.exec()
