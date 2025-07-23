from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from qfluentwidgets import MessageBoxBase, ScrollArea, CardWidget, CaptionLabel, StrongBodyLabel, SubtitleLabel, InfoBar, InfoBarPosition
from ..common.style_sheet import setStyleSheet
from ..common.signal_bus import signalBus


class BilibiliQualityCard(CardWidget):
    """B站视频质量选择卡片"""

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

        # 显示质量标识
        quality_text = self.quality_data.get('quality_desc', str(self.quality_data.get('quality', '')))
        self.quality_text = QLabel(quality_text)
        self.quality_text.setObjectName('qualityText')
        self.quality_text.setAlignment(Qt.AlignCenter)
        self.quality_layout.addWidget(self.quality_text)

        # 信息区域
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(2)

        # 分辨率和帧率
        self.resolution_layout = QHBoxLayout()
        self.resolution_layout.setSpacing(8)

        resolution = f"{self.quality_data.get('width', 0)}x{self.quality_data.get('height', 0)}"
        self.resolution_label = StrongBodyLabel(resolution)
        self.resolution_label.setObjectName('resolutionLabel')
        self.resolution_layout.addWidget(self.resolution_label)

        if self.quality_data.get('frame_rate'):
            self.fps_label = CaptionLabel(f"{self.quality_data['frame_rate']}fps")
            self.fps_label.setObjectName('fpsLabel')
            self.resolution_layout.addWidget(self.fps_label)

        self.resolution_layout.addStretch()
        self.info_layout.addLayout(self.resolution_layout)

        # 详细信息
        codec = self.quality_data.get('codecs', 'unknown')
        bandwidth = self.quality_data.get('bandwidth', 0)
        if bandwidth > 0:
            bandwidth_mb = bandwidth / 1000000
            details = f"{bandwidth_mb:.1f}Mbps • {codec}"
        else:
            details = codec
        self.details_label = CaptionLabel(details)
        self.details_label.setObjectName('detailsLabel')
        self.info_layout.addWidget(self.details_label)

        self.hboxLayout.addLayout(self.info_layout)
        self.hboxLayout.addStretch()

        # 文件大小和格式
        self.size_layout = QVBoxLayout()
        self.size_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 估算文件大小（基于带宽）
        if bandwidth > 0:
            # 假设视频时长为3分钟（180秒）
            estimated_size_mb = (bandwidth * 180) / (8 * 1000000)
            if estimated_size_mb > 1000:
                size_text = f"{estimated_size_mb/1000:.1f}GB"
            else:
                size_text = f"{estimated_size_mb:.1f}MB"
        else:
            size_text = "未知"
        
        self.size_label = StrongBodyLabel(size_text)
        self.size_label.setObjectName('sizeLabel')
        self.size_label.setAlignment(Qt.AlignRight)
        self.size_layout.addWidget(self.size_label)

        format_text = "MP4"
        self.format_label = CaptionLabel(format_text)
        self.format_label.setObjectName('formatLabel')
        self.format_label.setAlignment(Qt.AlignRight)
        self.size_layout.addWidget(self.format_label)

        self.hboxLayout.addLayout(self.size_layout)
        
        # 应用样式
        self.applyStyles()

    def getQualityType(self):
        """根据质量返回质量类型"""
        quality = self.quality_data.get('quality', 0)
        if quality >= 80:  # 1080P及以上
            return 'high'
        elif quality >= 64:  # 720P
            return 'medium'
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
            quality = self.quality_data.get('quality', 0)
            if quality >= 80:
                border_color = QColor(139, 92, 246)  # 紫色
            elif quality >= 64:
                border_color = QColor(59, 130, 246)  # 蓝色
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


class BilibiliQualityDialog(MessageBoxBase):
    """B站视频质量选择对话框"""

    def __init__(self, video_info_dict=None, parent=None):
        super().__init__(parent)
        
        self.video_info_dict = video_info_dict or {}
        self.selected_quality = None

        self.titleLabel = SubtitleLabel('选择B站视频质量', self)
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
        self.setObjectName('bilibiliQualityDialog')
        self.scrollWidget.setObjectName('scrollWidget')
        setStyleSheet(self.scrollArea, 'video_dialog')
        setStyleSheet(self.scrollWidget, 'video_dialog')

    def setupData(self):
        """设置B站视频质量数据"""
        # 从视频信息中提取质量选项
        play_info = self.video_info_dict.get('play_info', {})
        
        if 'dash' in play_info:
            # DASH格式
            dash_data = play_info['dash']
            video_streams = dash_data.get('video', [])
            audio_streams = dash_data.get('audio', [])
            
            # 处理视频流
            self.data = []
            for video in video_streams:
                quality_data = {
                    'quality': video.get('id', 0),
                    'quality_desc': self._get_quality_desc(video.get('id', 0)),
                    'width': video.get('width', 0),
                    'height': video.get('height', 0),
                    'frame_rate': video.get('frame_rate', ''),
                    'codecs': video.get('codecs', ''),
                    'bandwidth': video.get('bandwidth', 0),
                    'base_url': video.get('base_url', ''),
                    'backup_url': video.get('backup_url', []),
                    'type': 'video'
                }
                self.data.append(quality_data)
            
            # 添加音频选项
            if audio_streams:
                best_audio = max(audio_streams, key=lambda x: x.get('bandwidth', 0))
                audio_data = {
                    'quality': 0,
                    'quality_desc': '音频',
                    'width': 0,
                    'height': 0,
                    'frame_rate': '',
                    'codecs': best_audio.get('codecs', ''),
                    'bandwidth': best_audio.get('bandwidth', 0),
                    'base_url': best_audio.get('base_url', ''),
                    'backup_url': best_audio.get('backup_url', []),
                    'type': 'audio'
                }
                self.data.append(audio_data)
        
        elif 'durl' in play_info:
            # 传统格式
            durl_data = play_info['durl']
            if durl_data:
                quality_data = {
                    'quality': play_info.get('quality', 32),
                    'quality_desc': self._get_quality_desc(play_info.get('quality', 32)),
                    'width': 0,
                    'height': 0,
                    'frame_rate': '',
                    'codecs': 'H.264',
                    'bandwidth': 0,
                    'base_url': durl_data[0].get('url', ''),
                    'backup_url': durl_data[0].get('backup_url', []),
                    'type': 'video'
                }
                self.data = [quality_data]
        # 按质量排序（高质量在前）
        self.data.sort(key=lambda x: x.get('quality', 0), reverse=True)

        # 创建卡片
        self.cards = []
        for i, data in enumerate(self.data):
            card = BilibiliQualityCard(data, self.scrollWidget)
            card.clicked.connect(lambda checked=False, quality_data=data: self.onCardClicked(quality_data))
            self.cards.append(card)
            self.scrollLayout.addWidget(card)

        # 添加弹性空间
        self.scrollLayout.addStretch()
    
    def _get_quality_desc(self, quality_id):
        """根据质量ID获取描述"""
        quality_map = {
            120: '4K',
            116: '1080P60',
            112: '1080P+',
            80: '1080P',
            74: '720P60',
            64: '720P',
            48: '720P',
            32: '480P',
            16: '360P',
            6: '240P'
        }
        return quality_map.get(quality_id, f'质量{quality_id}')
    
    def onCardClicked(self, quality_data):
        """处理卡片点击事件"""
        self.selected_quality = quality_data
        
        # 获取主窗口并直接显示下载开始提示
        main_window = self.window()
        InfoBar.success(
            title="开始下载",
            content=f"正在下载 {self._get_quality_desc(quality_data.get('quality', 0))} B站视频...",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=main_window
        )
        
        # 发送信号并关闭对话框
        signalBus.bilibiliQualitySelectedSig.emit(quality_data)
        self.accept()  # 确认关闭
    
    def reject(self):
        """重写reject方法，处理取消操作"""
        super().reject()