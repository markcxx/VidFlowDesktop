# coding:utf-8
# @Author  : Mark
# @FileName: skeleton_widget.py

from PyQt5.QtCore import QPropertyAnimation, QRectF, pyqtProperty, Qt
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPainterPath, QBrush
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import FlowLayout


class SkeletonBase(QWidget):
    """骨架屏基类，提供统一的光带动画效果"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shimmer_position = -100
        self._animation = None
        self._is_animating = False
        self.setFixedHeight(20)  # 默认高度

    @pyqtProperty(float)
    def shimmer_position(self):
        return self._shimmer_position

    @shimmer_position.setter
    def shimmer_position(self, value):
        self._shimmer_position = value
        self.update()

    def start_animation(self):
        """开始光带动画"""
        if self._animation:
            self._animation.stop()

        self._animation = QPropertyAnimation(self, b"shimmer_position")
        self._animation.setDuration(1000)
        self._animation.setStartValue(-100)
        self._animation.setEndValue(self.width() + 100)
        self._animation.setLoopCount(-1)  # 无限循环
        self._animation.start()
        self._is_animating = True

    def stop_animation(self):
        """停止光带动画"""
        if self._animation:
            self._animation.stop()
        self._is_animating = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._is_animating:
            # 重新启动动画以适应新尺寸
            self.start_animation()

    def draw_shimmer(self, painter, rect):
        """绘制光带效果"""
        # 创建渐变
        gradient = QLinearGradient()
        gradient.setStart(self._shimmer_position - 50, 0)
        gradient.setFinalStop(self._shimmer_position + 50, 0)

        # 设置渐变颜色
        gradient.setColorAt(0, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.5, QColor(255, 255, 255, 80))
        gradient.setColorAt(1, QColor(255, 255, 255, 0))

        # 绘制光带
        painter.fillRect(rect, QBrush(gradient))


class SkeletonItem(SkeletonBase):
    """基础骨架项 - 矩形"""

    def __init__(self, width=100, height=20, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._background_color = QColor(210, 210, 210)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # 绘制背景
        painter.fillRect(rect, self._background_color)

        # 绘制光带
        self.draw_shimmer(painter, rect)


class RoundedRectSkeletonItem(SkeletonBase):
    """圆角矩形骨架项"""

    def __init__(self, width=100, height=20, radius=8, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._radius = radius
        self._background_color = QColor(210, 210, 210)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect())

        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)

        # 绘制背景
        painter.fillPath(path, self._background_color)

        # 设置裁剪区域并绘制光带
        painter.setClipPath(path)
        self.draw_shimmer(painter, self.rect())


class CircleSkeletonItem(SkeletonBase):
    """圆形骨架项"""

    def __init__(self, diameter=40, parent=None):
        super().__init__(parent)
        self.setFixedSize(diameter, diameter)
        self._background_color = QColor(210, 210, 210)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect())

        # 创建圆形路径
        path = QPainterPath()
        path.addEllipse(rect)

        # 绘制背景
        painter.fillPath(path, self._background_color)

        # 设置裁剪区域并绘制光带
        painter.setClipPath(path)
        self.draw_shimmer(painter, self.rect())


class SkeletonContainer(QWidget):
    """骨架容器基类，提供整体光带效果"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shimmer_position = -100
        self._animation = None
        self._skeleton_items = []
        self._is_animating = False

    @pyqtProperty(float)
    def shimmer_position(self):
        return self._shimmer_position

    @shimmer_position.setter
    def shimmer_position(self, value):
        self._shimmer_position = value
        # 更新所有子骨架项的光带位置
        for item in self._skeleton_items:
            if hasattr(item, '_shimmer_position'):
                item._shimmer_position = value
                item.update()

    def add_skeleton_item(self, item):
        """添加骨架项到容器"""
        if isinstance(item, SkeletonBase):
            self._skeleton_items.append(item)
            # 停止子项的独立动画
            item.stop_animation()

    def start_animation(self):
        """开始整体光带动画"""
        if self._animation:
            self._animation.stop()

        self._animation = QPropertyAnimation(self, b"shimmer_position")
        self._animation.setDuration(1000)
        self._animation.setStartValue(-100)
        self._animation.setEndValue(self.width() + 100)
        self._animation.setLoopCount(-1)
        self._animation.start()
        self._is_animating = True

    def stop_animation(self):
        """停止整体光带动画"""
        if self._animation:
            self._animation.stop()
        self._is_animating = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._is_animating:
            self.start_animation()


class CirclePersonaSkeleton(SkeletonContainer):
    """圆形头像骨架"""

    def __init__(self, avatar_size=50, parent=None):
        super().__init__(parent)
        self.setup_ui(avatar_size)

    def setup_ui(self, avatar_size):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 圆形头像
        self.avatar = CircleSkeletonItem(avatar_size)
        layout.addWidget(self.avatar)
        self.add_skeleton_item(self.avatar)

        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # 姓名
        self.name_skeleton = RoundedRectSkeletonItem(120, 16, 4)
        info_layout.addWidget(self.name_skeleton)
        self.add_skeleton_item(self.name_skeleton)

        # 描述
        self.desc_skeleton = RoundedRectSkeletonItem(180, 14, 4)
        info_layout.addWidget(self.desc_skeleton)
        self.add_skeleton_item(self.desc_skeleton)

        info_layout.addStretch()
        layout.addLayout(info_layout)
        layout.addStretch()

        self.setFixedHeight(avatar_size + 20)


class SquarePersonaSkeleton(SkeletonContainer):
    """方形头像骨架"""

    def __init__(self, avatar_size=50, parent=None):
        super().__init__(parent)
        self.setup_ui(avatar_size)

    def setup_ui(self, avatar_size):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 方形头像（圆角矩形）
        self.avatar = RoundedRectSkeletonItem(avatar_size, avatar_size, 8)
        layout.addWidget(self.avatar)
        self.add_skeleton_item(self.avatar)

        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # 姓名
        self.name_skeleton = RoundedRectSkeletonItem(120, 16, 4)
        info_layout.addWidget(self.name_skeleton)
        self.add_skeleton_item(self.name_skeleton)

        # 描述
        self.desc_skeleton = RoundedRectSkeletonItem(180, 14, 4)
        info_layout.addWidget(self.desc_skeleton)
        self.add_skeleton_item(self.desc_skeleton)

        info_layout.addStretch()
        layout.addLayout(info_layout)
        layout.addStretch()

        self.setFixedHeight(avatar_size + 20)


class ArticleSkeleton(SkeletonContainer):
    """文章骨架"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # 标题
        self.title_skeleton = RoundedRectSkeletonItem(300, 20, 4)
        layout.addWidget(self.title_skeleton)
        self.add_skeleton_item(self.title_skeleton)

        # 副标题
        self.subtitle_skeleton = RoundedRectSkeletonItem(250, 16, 4)
        layout.addWidget(self.subtitle_skeleton)
        self.add_skeleton_item(self.subtitle_skeleton)

        # 内容行
        for i in range(3):
            width = 400 if i < 2 else 300  # 最后一行短一些
            content_skeleton = RoundedRectSkeletonItem(width, 14, 4)
            layout.addWidget(content_skeleton)
            self.add_skeleton_item(content_skeleton)

        self.setFixedHeight(150)

class Skeleton:
    """骨架屏工厂类"""

    @staticmethod
    def create_item(width=100, height=20):
        """创建基础矩形骨架项"""
        return SkeletonItem(width, height)

    @staticmethod
    def create_rounded_item(width=100, height=20, radius=8):
        """创建圆角矩形骨架项"""
        return RoundedRectSkeletonItem(width, height, radius)

    @staticmethod
    def create_circle_item(diameter=40):
        """创建圆形骨架项"""
        return CircleSkeletonItem(diameter)

    @staticmethod
    def create_circle_persona(avatar_size=50):
        """创建圆形头像骨架"""
        return CirclePersonaSkeleton(avatar_size)

    @staticmethod
    def create_square_persona(avatar_size=50):
        """创建方形头像骨架"""
        return SquarePersonaSkeleton(avatar_size)

    @staticmethod
    def create_article():
        """创建文章骨架"""
        return ArticleSkeleton()
