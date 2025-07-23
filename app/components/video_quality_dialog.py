from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from qfluentwidgets import MessageBoxBase, ScrollArea, CardWidget, CaptionLabel, StrongBodyLabel, SubtitleLabel, InfoBar, InfoBarPosition
from ..common.signal_bus import signalBus
from ..common.style_sheet import setStyleSheet



class VideoQualityCard(CardWidget):
    """视频质量选择卡片"""

    def __init__(self, quality_data, parent=None):
        super().__init__(parent)
        self.quality_data = quality_data
        self.is_hovered = False

        self.setFixedHeight(80)
        self.setCursor(Qt.PointingHandCursor)

        # 主布局
        self.hboxLayout = QHBoxLayout(self)
        self.hboxLayout.setContentsMargins(16, 12, 16, 12)
        self.hboxLayout.setSpacing(12)

        # 质量标识区域
        self.quality_frame = QFrame(self)
        self.quality_frame.setObjectName('qualityFrame')
        self.quality_frame.setFixedSize(50, 50)

        # 使用动态属性设置背景色
        self.quality_frame.setProperty('qualityType', self.getQualityType())

        self.quality_layout = QVBoxLayout(self.quality_frame)
        self.quality_layout.setContentsMargins(0, 0, 0, 0)
        self.quality_layout.setAlignment(Qt.AlignCenter)
        self.hboxLayout.addWidget(self.quality_frame)

        self.quality_text = QLabel(
            self.quality_data['resolution'].split('p')[0] + 'p' if 'p' in self.quality_data['resolution'] else 'Audio')
        self.quality_text.setObjectName('qualityText')
        self.quality_text.setAlignment(Qt.AlignCenter)
        self.quality_layout.addWidget(self.quality_text)

        # 信息区域
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(2)

        # 分辨率和帧率
        self.resolution_layout = QHBoxLayout()
        self.resolution_layout.setSpacing(8)

        self.resolution_label = StrongBodyLabel(self.quality_data['resolution'])
        self.resolution_label.setObjectName('resolutionLabel')
        self.resolution_layout.addWidget(self.resolution_label)

        if self.quality_data['fps'] > 0:
            self.fps_label = CaptionLabel(f"{self.quality_data['fps']}fps")
            self.fps_label.setObjectName('fpsLabel')
            self.resolution_layout.addWidget(self.fps_label)

        self.resolution_layout.addStretch()
        self.info_layout.addLayout(self.resolution_layout)

        # 详细信息
        self.details = f"{self.quality_data['bitrate']} • {self.quality_data['encoding']}"
        self.details_label = CaptionLabel(self.details)
        self.details_label.setObjectName('detailsLabel')
        self.info_layout.addWidget(self.details_label)

        self.hboxLayout.addLayout(self.info_layout)
        self.hboxLayout.addStretch()

        # 文件大小和格式
        self.size_layout = QVBoxLayout()
        self.size_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.size_label = StrongBodyLabel(self.quality_data['size'])
        self.size_label.setObjectName('sizeLabel')
        self.size_label.setAlignment(Qt.AlignRight)
        self.size_layout.addWidget(self.size_label)

        self.format_label = CaptionLabel(self.quality_data['format'].upper())
        self.format_label.setObjectName('formatLabel')
        self.format_label.setAlignment(Qt.AlignRight)
        self.size_layout.addWidget(self.format_label)

        self.hboxLayout.addLayout(self.size_layout)
        
        # 应用样式
        self.applyStyles()

    def getQualityType(self):
        """根据分辨率返回质量类型"""
        resolution = self.quality_data['resolution']
        if '4K' in resolution or '1080p' in resolution:
            return 'high'
        elif '720p' in resolution:
            return 'medium'
        elif 'Audio' in resolution or '音频' in resolution:
            return 'audio'
        else:
            return 'low'
    
    def applyStyles(self):
        """应用样式表到卡片"""
        setStyleSheet(self, 'video_dialog')

    def enterEvent(self, event):
        """鼠标进入事件"""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """自定义绘制事件"""
        super().paintEvent(event)

        if self.is_hovered:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # 绘制悬停边框
            resolution = self.quality_data['resolution']
            if '4K' in resolution or '1080p' in resolution:
                border_color = QColor(139, 92, 246)  # 紫色
            elif '720p' in resolution:
                border_color = QColor(59, 130, 246)  # 蓝色
            elif 'Audio' in resolution or '音频' in resolution:
                border_color = QColor(245, 158, 11)  # 橙色
            else:
                border_color = QColor(16, 185, 129)  # 绿色

            pen = QPen(border_color, 2)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class VideoQualityDialog(MessageBoxBase):

    def __init__(self, video_info_dict=None, parent=None):
        super().__init__(parent)
        
        self.video_info_dict = video_info_dict or {}
        self.selected_quality = None

        self.titleLabel = SubtitleLabel('选择下载质量', self)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")

        self.scrollArea = ScrollArea(self)
        self.scrollArea.setFixedSize(500, 300)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 滚动区域内容
        self.scrollWidget = QWidget(self)
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setSpacing(12)
        self.scrollLayout.setContentsMargins(20, 15, 20, 15)
        self.scrollLayout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # 设置滚动区域属性
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # 添加到主布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addWidget(self.scrollArea)
        self.viewLayout.addSpacing(15)

        # 设置弹窗大小
        self.widget.setFixedSize(540, 480)

        self.setupData()
        self.setQss()

    def setQss(self):
        self.setObjectName('videoQualityDialog')
        self.scrollWidget.setObjectName('scrollWidget')
        setStyleSheet(self.scrollArea, 'video_dialog')
        setStyleSheet(self.scrollWidget, 'video_dialog')

    def setupData(self):
        """设置数据"""
        if (self.video_info_dict.get('platform') == '抖音' and 
            'video_quality_options' in self.video_info_dict):
            self.data = self.video_info_dict['video_quality_options']
        # 创建卡片
        self.cards = []
        for i, data in enumerate(self.data):
            card = VideoQualityCard(data, self.scrollWidget)
            card.clicked.connect(lambda checked=False, quality_data=data: self.onCardClicked(quality_data))
            self.cards.append(card)
            self.scrollLayout.addWidget(card)

        # 添加弹性空间
        self.scrollLayout.addStretch()
    
    def onCardClicked(self, quality_data):
        """处理卡片点击事件"""
        self.selected_quality = quality_data
        InfoBar.success(
            title="开始下载",
            content=f"正在下载 {quality_data.get('resolution', '未知质量')} 视频...",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
        
        # 发送信号并关闭对话框
        signalBus.videoQualitySelectedSig.emit(quality_data)
        self.accept()  # 确认关闭
    
    def reject(self):
        """重写reject方法，处理取消操作"""
        super().reject()

