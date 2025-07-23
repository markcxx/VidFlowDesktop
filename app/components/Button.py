# coding:utf-8
# @Time    : 2025/4/24 下午1:43
# @Author  : Mark
# @FileName: Button.py
import os

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QIcon, QPainter, QPen, QPainterPath, QColor
from PyQt5.QtSvg import QSvgRenderer
from qfluentwidgets import ToolButton, FluentIcon
from qframelesswindow import TitleBarButton
from qframelesswindow.titlebar.title_bar_buttons import TitleBarButtonState, SvgTitleBarButton


class RoundedToolButton(ToolButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
                ToolButton {
                    color: black;
                    border-radius: 30px;
                    background: transparent;
                    outline: none;
                }

                ToolButton:disabled {
                    color: rgba(0, 0, 0, 0.36);
                    background: rgba(249, 249, 249, 0.3);
                    border: 1px solid rgba(0, 0, 0, 0.06);
                    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
                }
        """)
        self.normal_icon = QIcon()
        self.hover_icon = QIcon()

    def setIcon(self, icon):
        if isinstance(icon, str):
            # 处理图标路径字符串
            self.normal_icon = QIcon(icon)
            base, ext = os.path.splitext(icon)
            hover_path = f"{base}-hover{ext}"
            if os.path.exists(hover_path):
                self.hover_icon = QIcon(hover_path)
            else:
                self.hover_icon = self.normal_icon
        else:
            self.normal_icon = icon
            self.hover_icon = icon

        super().setIcon(self.normal_icon)

    def setHoverIcon(self, icon):
        self.hover_icon = icon

    def enterEvent(self, event):
        super().enterEvent(event)
        if not self.hover_icon.isNull():
            super().setIcon(self.hover_icon)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        super().setIcon(self.normal_icon)


class MinimizeButton(TitleBarButton):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(40, 40)

    def paintEvent(self, e):
        painter = QPainter(self)
        color, bgColor = self._getColors()

        painter.setBrush(bgColor)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

        painter.setBrush(Qt.NoBrush)
        pen = QPen(color, 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawLine(12, 20, 28, 20)


class MaximizeButton(TitleBarButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._isMax = False
        self.setFixedSize(40, 40)

    def setMaxState(self, isMax):
        """ update the maximized state and icon """
        if self._isMax == isMax:
            return

        self._isMax = isMax
        self.setState(TitleBarButtonState.NORMAL)

    def paintEvent(self, e):
        painter = QPainter(self)
        color, bgColor = self._getColors()

        # draw background
        painter.setBrush(bgColor)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

        # draw icon
        painter.setBrush(Qt.NoBrush)
        pen = QPen(color, 1)
        pen.setCosmetic(True)
        painter.setPen(pen)

        r = self.devicePixelRatioF()
        painter.scale(1 / r, 1 / r)
        if not self._isMax:
            painter.drawRect(int(14 * r), int(14 * r), int(12 * r), int(12 * r))
        else:
            painter.drawRect(int(14 * r), int(16 * r), int(10 * r), int(10 * r))
            x0 = int(14 * r) + int(2 * r)
            y0 = 16 * r
            dw = int(3 * r)
            path = QPainterPath(QPointF(x0, y0))
            path.lineTo(x0, y0 - dw)
            path.lineTo(x0 + 10 * r, y0 - dw)
            path.lineTo(x0 + 10 * r, y0 - dw + 10 * r)
            path.lineTo(x0 + 10 * r - dw, y0 - dw + 10 * r)
            painter.drawPath(path)


class CloseButton(SvgTitleBarButton):
    """ Close button """

    def __init__(self, parent=None):
        super().__init__(":/qframelesswindow/close.svg", parent)
        self.setFixedSize(48, 38)
        self.setHoverColor(Qt.white)
        self.setPressedColor(Qt.white)
        self.setHoverBackgroundColor(QColor(0, 0, 0, 26))
        self.setPressedBackgroundColor(QColor(0, 0, 0, 51))

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        color, bgColor = self._getColors()

        # draw background
        painter.setBrush(bgColor)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

        # draw icon
        color = color.name()
        pathNodes = self._svgDom.elementsByTagName('path')
        for i in range(pathNodes.length()):
            element = pathNodes.at(i).toElement()
            element.setAttribute('stroke', color)

        renderer = QSvgRenderer(self._svgDom.toByteArray())
        renderer.render(painter, QRectF(self.rect()))
