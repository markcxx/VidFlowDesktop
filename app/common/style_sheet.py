# coding:utf-8
from .config import config, Theme
from PyQt5.QtCore import QFile
from PyQt5.QtWidgets import QWidget


def getStyleSheet(file: str, theme=Theme.AUTO):
    """ get style sheet

    Parameters
    ----------
    file: str
        qss file name, without `.qss` suffix

    theme: Theme
        the theme of style sheet
    """
    theme = config.theme if theme == Theme.AUTO else theme
    # theme = Theme.DARK
    f = QFile(f":/qss/{theme.value.lower()}/{file}.qss")
    f.open(QFile.ReadOnly)
    qss = str(f.readAll(), encoding='utf-8')
    f.close()
    return qss


def setStyleSheet(widget: QWidget, file: str, theme=Theme.AUTO):
    """ set the style sheet of widget

    Parameters
    ----------
    widget: QWidget
        the widget to set style sheet

    file: str
        qss file name, without `.qss` suffix

    theme: Theme
        the theme of style sheet
    """
    widget.setStyleSheet(getStyleSheet(file, theme))


def setCustomStyleSheetFromFile(widget: QWidget, file: str, theme=Theme.AUTO):
    """ set custom style sheet for qfluentwidgets components from qss file

    Parameters
    ----------
    widget: QWidget
        the qfluentwidgets component to set custom style sheet

    file: str
        qss file name, without `.qss` suffix

    theme: Theme
        the theme of style sheet
    """
    from qfluentwidgets.common.style_sheet import setCustomStyleSheet
    
    qss_content = getStyleSheet(file, theme)
    # 对于 qfluentwidgets 组件，light 和 dark 主题使用相同的样式内容
    setCustomStyleSheet(widget, qss_content, qss_content)
