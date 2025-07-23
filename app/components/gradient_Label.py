from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QRect


class GradientLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.gradient_colors = [(0.0, QColor(37, 99, 235)), (1.0, QColor(147, 51, 234))]  # 蓝色到紫色

    def setGradientColors(self, colors):
        """设置渐变颜色 colors: [(position, QColor), ...]"""
        self.gradient_colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 创建线性渐变
        gradient = QLinearGradient(0, 0, self.width(), 0)
        for position, color in self.gradient_colors:
            gradient.setColorAt(position, color)

        # 设置画笔为渐变色
        pen = QPen()
        pen.setBrush(gradient)
        painter.setPen(pen)

        # 设置字体
        painter.setFont(self.font())

        # 绘制文字
        painter.drawText(self.rect(), self.alignment(), self.text())