# coding:utf-8
# @Time    : 2025/4/18 下午10:35
# @Author  : Mark
# @FileName: PlayListCover.py
import os
import sys
from typing import Union

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QToolButton
from PyQt5.QtGui import QPixmap, QPainterPath, QPainter, QMouseEvent, QIcon, QColor
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QSize, QAbstractAnimation, QPoint, QRectF

from PyQt5.QtWidgets import QGraphicsOpacityEffect
from .Button import RoundedToolButton
from ..common.vidflowicon import VidFlowIcon


class RoundedLabel(QLabel):
    """
    QLabel subclass that rounds the top-left and top-right corners of the pixmap.
    """

    def __init__(self, parent=None, radius=10):
        super().__init__(parent)
        self._radius = radius
        self._original_pixmap = None

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = value
        # reapply rounding if a pixmap is already set
        if self._original_pixmap:
            self.setPixmap(self._original_pixmap)

    def setPixmap(self, pixmap):
        """
        Overrides QLabel.setPixmap to apply rounding on the top corners.
        """
        if not isinstance(pixmap, QPixmap):
            super().setPixmap(pixmap)
            return

        self._original_pixmap = pixmap
        rounded = self._rounded_corners(pixmap, self._radius)
        super().setPixmap(rounded)

    def _rounded_corners(self, pixmap, radius):
        """
        Returns a new QPixmap with all four corners rounded by the given radius.
        """
        size = pixmap.size()
        result = QPixmap(size)
        result.fill(Qt.transparent)

        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        w, h = size.width(), size.height()
        r = radius

        path.addRoundedRect(0, 0, w, h, r, r)

        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return result


class VideoCover(QWidget):
    played = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setCursor(Qt.PointingHandCursor)

        self.layout = QVBoxLayout(self)
        self.coverLabel = RoundedLabel(self)
        self.coverLabel.setObjectName("coverLabel")
        # self.coverLabel.setFixedSize(180, 270)
        self.coverLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.coverLabel)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.mask_layer = QWidget(self)
        self.mask_layer.setObjectName("maskLayer")
        self.mask_layer.resize(self.coverLabel.width(), self.coverLabel.height())
        self.mask_layer.setVisible(False)
        self.mask_layer.setStyleSheet("background-color: rgba(0, 0, 0, 0.4);border-radius:15px")

        self.mask_layout = QVBoxLayout(self.mask_layer)
        self.mask_layout.setAlignment(Qt.AlignCenter)
        self.playButton = RoundedToolButton(self.mask_layer)
        self.playButton.setIcon(VidFlowIcon.PLAY.icon())
        self.playButton.setMinimumSize(60, 60)
        self.playButton.setIconSize(QSize(60, 60))
        self.mask_layout.addWidget(self.playButton)

        self.opacity_effect = QGraphicsOpacityEffect(self.mask_layer)
        self.mask_layer.setGraphicsEffect(self.opacity_effect)
        self.mask_layer.move(self.x(), self.y())
        self.enter_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.enter_animation.setDuration(300)
        self.enter_animation.setStartValue(0.0)
        self.enter_animation.setEndValue(1)
        self.enter_animation.setEasingCurve(QEasingCurve.OutQuad)

        self.leave_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.leave_animation.setDuration(300)
        self.leave_animation.setStartValue(1)
        self.leave_animation.setEndValue(0.0)
        self.leave_animation.setEasingCurve(QEasingCurve.InQuad)

        self.playButton.clicked.connect(lambda: self.played.emit())

    def enterEvent(self, event):
        self.enter_animation.start()
        self.mask_layer.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.leave_animation.start()
        super().leaveEvent(event)

    def create_scaled_pixmap(self, image_path):
        """创建保持比例的居中显示图片"""
        # 使用父组件的尺寸作为目标尺寸
        target_size = self.size()
        if target_size.width() == 0 or target_size.height() == 0:
            target_size = QSize(300, 200)  # 默认尺寸
            
        original = QPixmap(image_path)
        if original.isNull():
            return QPixmap(target_size)

        # 计算缩放比例，选择较大的比例以填充更多空间
        scale_x = target_size.width() / original.width()
        scale_y = target_size.height() / original.height()
        scale = max(scale_x, scale_y)
        
        # 计算缩放后的尺寸
        new_width = int(original.width() * scale)
        new_height = int(original.height() * scale)
        
        # 缩放图片
        scaled = original.scaled(
            new_width, new_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # 创建目标尺寸的画布，用背景色填充
        result = QPixmap(target_size)
        result.fill(QColor(240, 240, 240))  # 浅灰色背景
        
        # 将缩放后的图片居中绘制到画布上
        painter = QPainter(result)
        x = (target_size.width() - scaled.width()) // 2
        y = (target_size.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        
        return result

    def setImage(self, image_path: str):
        """修改封面图片方法"""
        scaled_pixmap = self.create_scaled_pixmap(image_path)
        self.coverLabel.setPixmap(scaled_pixmap)
    
    def setPixmap(self, pixmap: QPixmap):
        """直接设置QPixmap对象"""
        if pixmap and not pixmap.isNull():
            self.coverLabel.setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.mask_layer.setGeometry(
            self.coverLabel.geometry()
        )