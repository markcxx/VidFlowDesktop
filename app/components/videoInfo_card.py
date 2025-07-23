from datetime import datetime
import math
import os

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QRectF
from PyQt5.QtGui import QFont, QImage, QColor, QPainter, QPen, QPixmap, QBrush
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QGridLayout, QFrame, QLabel, QSizePolicy
from qfluentwidgets import CardWidget, CaptionLabel, AvatarWidget, TitleLabel, BodyLabel, PrimaryPushButton, PushButton, \
    ProgressBar, IconWidget, FluentIcon, FlowLayout, PillPushButton, InfoBar, InfoBarPosition

from .coloricon_widget import ColorIconWidget
from .videoCover_widget import VideoCover
from ..common.signal_bus import signalBus
from ..common.threadManager import VideoDownloadThread, AudioDownloadThread, BilibiliDownloadThread
from ..common.style_sheet import setStyleSheet, setCustomStyleSheetFromFile
from ..common.threadManager import ImageLoaderThread
from ..common.bilibili_login import BilibiliLogin
from ..common.vidflowicon import VidFlowIcon
from ..components.video_quality_dialog import VideoQualityDialog
from ..components.bilibili_quality_dialog import BilibiliQualityDialog


class ProgressAudioButton(PushButton):
    """带进度边框的音频下载按钮"""

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        if text:
            self.setText(text)
        self.progress = 0  # 进度值 0-100
        self.border_width = 2  # 边框宽度

    def setProgress(self, progress):
        """设置进度值"""
        self.progress = max(0, min(100, progress))
        self.update()  # 触发重绘

    def clearProgress(self):
        """清除进度"""
        self.progress = 0
        self.update()

    def paintEvent(self, event):
        """重写绘制事件，添加圆角矩形进度边框"""
        super().paintEvent(event)

        if self.progress > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # 设置画笔
            pen = QPen(QColor(0, 120, 215), self.border_width)  # 蓝色边框
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            # 计算绘制区域
            rect = self.rect()
            margin = self.border_width // 2
            border_radius = 5  # 圆角半径

            # 调整绘制区域以适应边框宽度
            draw_rect = rect.adjusted(margin, margin, -margin, -margin)
            

            
            # 计算路径总长度
            width = draw_rect.width()
            height = draw_rect.height()
            # 圆角矩形周长 = 直边长度 + 圆弧长度
            straight_length = 2 * (width + height - 4 * border_radius)
            arc_length = 2 * math.pi * border_radius
            total_length = straight_length + arc_length
            
            # 计算当前进度对应的长度
            progress_length = (self.progress / 100.0) * total_length
            
            # 绘制圆角矩形进度
            if progress_length > 0:
                current_length = 0
                
                # 1. 顶边（从左上角圆角结束到右上角圆角开始）
                top_edge_length = width - 2 * border_radius
                if progress_length > current_length and top_edge_length > 0:
                    if current_length + top_edge_length <= progress_length:
                        # 完整绘制顶边
                        painter.drawLine(
                            int(draw_rect.left() + border_radius), int(draw_rect.top()),
                            int(draw_rect.right() - border_radius), int(draw_rect.top())
                        )
                        current_length += top_edge_length
                    else:
                        # 部分绘制顶边
                        remaining = progress_length - current_length
                        painter.drawLine(
                            int(draw_rect.left() + border_radius), int(draw_rect.top()),
                            int(draw_rect.left() + border_radius + remaining), int(draw_rect.top())
                        )
                        current_length = progress_length
                
                # 2. 右上角圆弧
                right_top_arc_length = math.pi * border_radius / 2
                if progress_length > current_length:
                    if current_length + right_top_arc_length <= progress_length:
                        # 完整绘制右上角弧（90度）
                        arc_rect = QRectF(
                            draw_rect.right() - 2 * border_radius,
                            draw_rect.top(),
                            2 * border_radius,
                            2 * border_radius
                        )
                        painter.drawArc(arc_rect, 0 * 16, 90 * 16)  # 从0度到90度
                        current_length += right_top_arc_length
                    else:
                        # 部分绘制右上角弧
                        remaining = progress_length - current_length
                        angle_span = int((remaining / right_top_arc_length) * 90 * 16)
                        arc_rect = QRectF(
                            draw_rect.right() - 2 * border_radius,
                            draw_rect.top(),
                            2 * border_radius,
                            2 * border_radius
                        )
                        painter.drawArc(arc_rect, 0 * 16, angle_span)
                        current_length = progress_length
                
                # 3. 右边
                right_edge_length = height - 2 * border_radius
                if progress_length > current_length and right_edge_length > 0:
                    if current_length + right_edge_length <= progress_length:
                        # 完整绘制右边
                        painter.drawLine(
                            int(draw_rect.right()), int(draw_rect.top() + border_radius),
                            int(draw_rect.right()), int(draw_rect.bottom() - border_radius)
                        )
                        current_length += right_edge_length
                    else:
                        # 部分绘制右边
                        remaining = progress_length - current_length
                        painter.drawLine(
                            int(draw_rect.right()), int(draw_rect.top() + border_radius),
                            int(draw_rect.right()), int(draw_rect.top() + border_radius + remaining)
                        )
                        current_length = progress_length
                
                # 4. 右下角圆弧
                right_bottom_arc_length = math.pi * border_radius / 2
                if progress_length > current_length:
                    if current_length + right_bottom_arc_length <= progress_length:
                        # 完整绘制右下角弧
                        arc_rect = QRectF(
                            draw_rect.right() - 2 * border_radius,
                            draw_rect.bottom() - 2 * border_radius,
                            2 * border_radius,
                            2 * border_radius
                        )
                        painter.drawArc(arc_rect, 270 * 16, 90 * 16)  # 从270度到360度
                        current_length += right_bottom_arc_length
                    else:
                        # 部分绘制右下角弧
                        remaining = progress_length - current_length
                        angle_span = int((remaining / right_bottom_arc_length) * 90 * 16)
                        arc_rect = QRectF(
                            draw_rect.right() - 2 * border_radius,
                            draw_rect.bottom() - 2 * border_radius,
                            2 * border_radius,
                            2 * border_radius
                        )
                        painter.drawArc(arc_rect, 270 * 16, angle_span)
                        current_length = progress_length
                
                # 5. 底边
                bottom_edge_length = width - 2 * border_radius
                if progress_length > current_length and bottom_edge_length > 0:
                    if current_length + bottom_edge_length <= progress_length:
                        # 完整绘制底边（从右到左）
                        painter.drawLine(
                            int(draw_rect.right() - border_radius), int(draw_rect.bottom()),
                            int(draw_rect.left() + border_radius), int(draw_rect.bottom())
                        )
                        current_length += bottom_edge_length
                    else:
                        # 部分绘制底边
                        remaining = progress_length - current_length
                        painter.drawLine(
                            int(draw_rect.right() - border_radius), int(draw_rect.bottom()),
                            int(draw_rect.right() - border_radius - remaining), int(draw_rect.bottom())
                        )
                        current_length = progress_length
                
                # 6. 左下角圆弧
                left_bottom_arc_length = math.pi * border_radius / 2
                if progress_length > current_length:
                    if current_length + left_bottom_arc_length <= progress_length:
                        # 完整绘制左下角弧
                        arc_rect = QRectF(
                            draw_rect.left(),
                            draw_rect.bottom() - 2 * border_radius,
                            2 * border_radius,
                            2 * border_radius
                        )
                        painter.drawArc(arc_rect, 180 * 16, 90 * 16)  # 从180度到270度
                        current_length += left_bottom_arc_length
                    else:
                        # 部分绘制左下角弧
                        remaining = progress_length - current_length
                        angle_span = int((remaining / left_bottom_arc_length) * 90 * 16)
                        arc_rect = QRectF(
                            draw_rect.left(),
                            draw_rect.bottom() - 2 * border_radius,
                            2 * border_radius,
                            2 * border_radius
                        )
                        painter.drawArc(arc_rect, 180 * 16, angle_span)
                        current_length = progress_length
                
                # 7. 左边
                left_edge_length = height - 2 * border_radius
                if progress_length > current_length and left_edge_length > 0:
                    if current_length + left_edge_length <= progress_length:
                        # 完整绘制左边（从下到上）
                        painter.drawLine(
                            int(draw_rect.left()), int(draw_rect.bottom() - border_radius),
                            int(draw_rect.left()), int(draw_rect.top() + border_radius)
                        )
                        current_length += left_edge_length
                    else:
                        # 部分绘制左边
                        remaining = progress_length - current_length
                        painter.drawLine(
                            int(draw_rect.left()), int(draw_rect.bottom() - border_radius),
                            int(draw_rect.left()), int(draw_rect.bottom() - border_radius - remaining)
                        )
                        current_length = progress_length
                
                # 8. 左上角圆弧
                left_top_arc_length = math.pi * border_radius / 2
                if progress_length > current_length:
                    if current_length + left_top_arc_length <= progress_length:
                        # 完整绘制左上角弧
                        arc_rect = QRectF(
                            draw_rect.left(),
                            draw_rect.top(),
                            2 * border_radius,
                            2 * border_radius
                        )
                        painter.drawArc(arc_rect, 90 * 16, 90 * 16)  # 从90度到180度
                        current_length += left_top_arc_length
                    else:
                        # 部分绘制左上角弧
                        remaining = progress_length - current_length
                        angle_span = int((remaining / left_top_arc_length) * 90 * 16)
                        arc_rect = QRectF(
                            draw_rect.left(),
                            draw_rect.top(),
                            2 * border_radius,
                            2 * border_radius
                        )
                        painter.drawArc(arc_rect, 90 * 16, angle_span)
                        current_length = progress_length

            painter.end()


class VideoInfoCard(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.videoInfoDict = {}
        self.download_thread = None  # 下载线程
        self.audio_download_thread = None
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        # 连接下载信号
        signalBus.startVideoDownloadSig.connect(self.startDownload)
        signalBus.startAudioDownloadSig.connect(self.startAudioDownload)
        signalBus.startBilibiliDownloadSig.connect(self.startBilibiliDownload)

        # 视频封面区域
        self.videoCoverLabel = VideoCover(self)
        self.videoCoverLabel.setFixedSize(300, 200)

        # 视频详情区域
        self.detailsWidget = QWidget(self)
        self.detailsLayout = QVBoxLayout(self.detailsWidget)
        self.detailsLayout.setContentsMargins(24, 24, 24, 24)
        self.detailsLayout.setSpacing(16)

        # 标题和平台标签布局
        self.titleLayout = QHBoxLayout()
        self.titleLabel = TitleLabel("-", self.detailsWidget)
        self.titleLabel.setWordWrap(True)
        self.titleLabel.setMaximumHeight(60)
        self.titleLabel.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))

        self.platformBadge = CaptionLabel("-", self.detailsWidget)
        self.platformBadge.setAlignment(Qt.AlignCenter)
        self.platformBadge.setFixedSize(48, 24)

        self.titleLayout.addWidget(self.titleLabel, 1)
        self.titleLayout.addWidget(self.platformBadge)
        self.detailsLayout.addLayout(self.titleLayout)

        # 视频描述
        self.descriptionLabel = CaptionLabel("-", self.detailsWidget)
        self.descriptionLabel.setWordWrap(True)
        self.descriptionLabel.setMaximumHeight(72)
        self.descriptionLabel.setTextColor(QColor(147, 155, 166), QColor(147, 155, 166))
        self.descriptionLabel.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
        self.detailsLayout.addWidget(self.descriptionLabel)

        # 作者信息布局
        self.authorLayout = QHBoxLayout()
        self.avatar = AvatarWidget(self.detailsWidget)
        self.avatar.setRadius(20)
        self.avatar.setFixedSize(40, 40)

        self.authorInfoLayout = QVBoxLayout()
        self.authorInfoLayout.setSpacing(2)

        # 作者名称和认证布局
        self.authorNameLayout = QHBoxLayout()
        self.authorNameLayout.setSpacing(4)

        self.authorNameLabel = BodyLabel("-", self.detailsWidget)
        self.authorNameLabel.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))

        self.verifiedIcon = IconWidget(VidFlowIcon.VERIFIE, self.detailsWidget)
        self.verifiedIcon.setFixedSize(16, 16)

        self.authorNameLayout.addWidget(self.authorNameLabel)
        self.authorNameLayout.addWidget(self.verifiedIcon)
        self.authorNameLayout.addStretch()

        self.fansLabel = CaptionLabel("-", self.detailsWidget)
        self.fansLabel.setTextColor(QColor(147, 155, 166), QColor(147, 155, 166))
        self.fansLabel.setFont(QFont("Microsoft YaHei", 12, QFont.Medium))

        self.signatureLabel = CaptionLabel("-", self.detailsWidget)
        self.signatureLabel.setTextColor(QColor(147, 155, 166), QColor(147, 155, 166))
        self.signatureLabel.setFont(QFont("Microsoft YaHei", 11, QFont.Medium))

        self.authorInfoLayout.addLayout(self.authorNameLayout)
        self.authorInfoLayout.addWidget(self.fansLabel)
        self.authorInfoLayout.addWidget(self.signatureLabel)

        self.authorLayout.addWidget(self.avatar)
        self.authorLayout.addLayout(self.authorInfoLayout)
        self.authorLayout.addStretch()
        self.detailsLayout.addLayout(self.authorLayout)

        # 统计信息网格
        self.statsWidget = QWidget(self.detailsWidget)
        self.statsLayout = QGridLayout(self.statsWidget)
        self.statsLayout.setSpacing(16)

        # 创建统计项目
        self.heartStatWidget = CardWidget(self.statsWidget)
        self.heartStatWidget.setFixedHeight(100)
        self.heartStatLayout = QVBoxLayout(self.heartStatWidget)
        self.heartStatLayout.setAlignment(Qt.AlignCenter)
        self.heartStatLayout.setSpacing(8)
        self.heartIcon = ColorIconWidget(VidFlowIcon.HEART, self.heartStatWidget)
        self.heartIcon.setColor(QColor(255, 63, 51))
        self.heartIcon.setFixedSize(24, 24)
        self.heartCountLabel = BodyLabel("-", self.heartStatWidget)
        self.heartCountLabel.setAlignment(Qt.AlignCenter)
        self.heartTextLabel = CaptionLabel("点赞", self.heartStatWidget)
        self.heartTextLabel.setTextColor(QColor(147, 155, 166), QColor(147, 155, 166))
        self.heartTextLabel.setAlignment(Qt.AlignCenter)
        self.heartStatLayout.addWidget(self.heartIcon, 0, Qt.AlignCenter)
        self.heartStatLayout.addWidget(self.heartCountLabel)
        self.heartStatLayout.addWidget(self.heartTextLabel)

        self.commentStatWidget = CardWidget(self.statsWidget)
        self.commentStatWidget.setFixedHeight(100)
        self.commentStatLayout = QVBoxLayout(self.commentStatWidget)
        self.commentStatLayout.setAlignment(Qt.AlignCenter)
        self.commentStatLayout.setSpacing(8)
        self.commentIcon = ColorIconWidget(VidFlowIcon.COMMENT, self.commentStatWidget)
        self.commentIcon.setColor(QColor(59, 130, 246))
        self.commentIcon.setFixedSize(24, 24)
        self.commentCountLabel = BodyLabel("-", self.commentStatWidget)
        self.commentCountLabel.setAlignment(Qt.AlignCenter)
        self.commentTextLabel = CaptionLabel("评论", self.commentStatWidget)
        self.commentTextLabel.setTextColor(QColor(147, 155, 166), QColor(147, 155, 166))
        self.commentTextLabel.setAlignment(Qt.AlignCenter)
        self.commentStatLayout.addWidget(self.commentIcon, 0, Qt.AlignCenter)
        self.commentStatLayout.addWidget(self.commentCountLabel)
        self.commentStatLayout.addWidget(self.commentTextLabel)

        self.shareStatWidget = CardWidget(self.statsWidget)
        self.shareStatWidget.setFixedHeight(100)
        self.shareStatLayout = QVBoxLayout(self.shareStatWidget)
        self.shareStatLayout.setAlignment(Qt.AlignCenter)
        self.shareStatLayout.setSpacing(8)
        self.shareIcon = ColorIconWidget(VidFlowIcon.SHARE, self.shareStatWidget)
        self.shareIcon.setColor(QColor(109, 218, 149))
        self.shareIcon.setFixedSize(24, 24)
        self.shareCountLabel = BodyLabel("-", self.shareStatWidget)
        self.shareCountLabel.setAlignment(Qt.AlignCenter)
        self.shareTextLabel = CaptionLabel("分享", self.shareStatWidget)
        self.shareTextLabel.setTextColor(QColor(147, 155, 166), QColor(147, 155, 166))
        self.shareTextLabel.setAlignment(Qt.AlignCenter)
        self.shareStatLayout.addWidget(self.shareIcon, 0, Qt.AlignCenter)
        self.shareStatLayout.addWidget(self.shareCountLabel)
        self.shareStatLayout.addWidget(self.shareTextLabel)

        self.collectStatWidget = CardWidget(self.statsWidget)
        self.collectStatWidget.setFixedHeight(100)
        self.collectStatLayout = QVBoxLayout(self.collectStatWidget)
        self.collectStatLayout.setAlignment(Qt.AlignCenter)
        self.collectStatLayout.setSpacing(8)
        self.collectIcon = ColorIconWidget(VidFlowIcon.COLLECT, self.collectStatWidget)
        self.collectIcon.setColor(QColor(234, 179, 8))
        self.collectIcon.setFixedSize(24, 24)
        self.collectCountLabel = BodyLabel("-", self.collectStatWidget)
        self.collectCountLabel.setAlignment(Qt.AlignCenter)
        self.collectTextLabel = CaptionLabel("收藏", self.collectStatWidget)
        self.collectTextLabel.setTextColor(QColor(147, 155, 166), QColor(147, 155, 166))
        self.collectTextLabel.setAlignment(Qt.AlignCenter)
        self.collectStatLayout.addWidget(self.collectIcon, 0, Qt.AlignCenter)
        self.collectStatLayout.addWidget(self.collectCountLabel)
        self.collectStatLayout.addWidget(self.collectTextLabel)

        # 投币统计（仅B站显示）
        self.coinStatWidget = CardWidget(self.statsWidget)
        self.coinStatWidget.setFixedHeight(100)
        self.coinStatWidget.setVisible(False)  # 默认隐藏
        self.coinStatLayout = QVBoxLayout(self.coinStatWidget)
        self.coinStatLayout.setAlignment(Qt.AlignCenter)
        self.coinStatLayout.setSpacing(8)
        self.coinIcon = ColorIconWidget(VidFlowIcon.COIN, self.coinStatWidget)
        self.coinIcon.setColor(QColor(251, 114, 153))
        self.coinIcon.setFixedSize(24, 24)
        self.coinCountLabel = BodyLabel("-", self.coinStatWidget)
        self.coinCountLabel.setAlignment(Qt.AlignCenter)
        self.coinTextLabel = CaptionLabel("投币", self.coinStatWidget)
        self.coinTextLabel.setTextColor(QColor(147, 155, 166), QColor(147, 155, 166))
        self.coinTextLabel.setAlignment(Qt.AlignCenter)
        self.coinStatLayout.addWidget(self.coinIcon, 0, Qt.AlignCenter)
        self.coinStatLayout.addWidget(self.coinCountLabel)
        self.coinStatLayout.addWidget(self.coinTextLabel)

        self.statsLayout.addWidget(self.heartStatWidget, 0, 0)
        self.statsLayout.addWidget(self.commentStatWidget, 0, 1)
        self.statsLayout.addWidget(self.shareStatWidget, 0, 2)
        self.statsLayout.addWidget(self.collectStatWidget, 0, 3)
        self.statsLayout.addWidget(self.coinStatWidget, 0, 4)
        self.detailsLayout.addWidget(self.statsWidget)

        # 音乐信息
        self.musicWidget = QWidget(self.detailsWidget)
        self.musicLayout = QHBoxLayout(self.musicWidget)
        self.musicLayout.setSpacing(8)
        self.musicLayout.setContentsMargins(0, 0, 0, 0)

        self.musicIcon = IconWidget(FluentIcon.MUSIC, self.musicWidget)
        self.musicIcon.setFixedSize(16, 16)

        self.musicLabel = CaptionLabel("原声：", self.musicWidget)
        self.musicLabel.setFont(QFont('Microsoft Yahei', 10, QFont.Medium))

        self.musicAuthorLabel = BodyLabel("-", self.musicWidget)
        self.musicAuthorLabel.setFont(QFont('Microsoft Yahei', 11, QFont.Bold))

        self.musicLayout.addWidget(self.musicIcon)
        self.musicLayout.addWidget(self.musicLabel)
        self.musicLayout.addWidget(self.musicAuthorLabel)
        self.musicLayout.addStretch()
        self.detailsLayout.addWidget(self.musicWidget)

        # 发布时间信息
        self.publishTimeWidget = QWidget(self.detailsWidget)
        self.publishTimeLayout = QHBoxLayout(self.publishTimeWidget)
        self.publishTimeLayout.setSpacing(8)
        self.publishTimeLayout.setContentsMargins(0, 0, 0, 0)

        self.timeIcon = IconWidget(FluentIcon.CALENDAR, self.publishTimeWidget)
        self.timeIcon.setFixedSize(16, 16)

        self.timeLabel = CaptionLabel("发布时间：", self.publishTimeWidget)
        self.timeLabel.setFont(QFont('Microsoft Yahei', 10, QFont.Medium))

        self.publishTimeValueLabel = BodyLabel("-", self.publishTimeWidget)
        self.publishTimeValueLabel.setFont(QFont('Microsoft Yahei', 11, QFont.Bold))

        self.publishTimeLayout.addWidget(self.timeIcon)
        self.publishTimeLayout.addWidget(self.timeLabel)
        self.publishTimeLayout.addWidget(self.publishTimeValueLabel)
        self.publishTimeLayout.addStretch()
        self.detailsLayout.addWidget(self.publishTimeWidget)

        # 标签区域
        self.tagsContainer = QWidget(self.detailsWidget)
        self.tagsLayout = QVBoxLayout(self.tagsContainer)
        self.tagsLayout.setSpacing(8)

        # 标签标题
        self.tagsTitleLayout = QHBoxLayout()
        self.tagIcon = IconWidget(FluentIcon.TAG, self.tagsContainer)
        self.tagIcon.setFixedSize(16, 16)

        self.tagsTitle = CaptionLabel("标签：", self.tagsContainer)

        self.tagsTitleLayout.addWidget(self.tagIcon)
        self.tagsTitleLayout.addWidget(self.tagsTitle)
        self.tagsTitleLayout.addStretch()

        self.tagsLayout.addLayout(self.tagsTitleLayout)

        # 标签流式布局
        self.tagsFlowLayout = FlowLayout(needAni=False)
        self.tagsFlowLayout.setContentsMargins(0, 0, 0, 0)
        self.tagsFlowLayout.setVerticalSpacing(8)
        self.tagsFlowLayout.setHorizontalSpacing(8)

        self.tagsLayout.addLayout(self.tagsFlowLayout)
        self.detailsLayout.addWidget(self.tagsContainer)

        # 下载区域
        self.downloadContainer = QWidget(self.detailsWidget)
        self.downloadLayout = QVBoxLayout(self.downloadContainer)
        self.downloadLayout.setSpacing(12)

        # 进度条区域（默认隐藏）
        self.progressWidget = QWidget(self.downloadContainer)
        self.progressLayout = QVBoxLayout(self.progressWidget)
        self.progressLayout.setSpacing(8)

        self.progressInfoLayout = QHBoxLayout()
        self.progressLabel = CaptionLabel("视频下载进度", self.progressWidget)

        self.progressPercent = CaptionLabel("0%", self.progressWidget)

        self.progressInfoLayout.addWidget(self.progressLabel)
        self.progressInfoLayout.addWidget(self.progressPercent)
        self.progressInfoLayout.addStretch()

        self.progressLayout.addLayout(self.progressInfoLayout)

        self.progressBar = ProgressBar(self.progressWidget)
        self.progressBar.setFixedHeight(8)
        self.progressBar.setValue(0)
        self.progressLayout.addWidget(self.progressBar)

        self.progressWidget.hide()
        self.downloadLayout.addWidget(self.progressWidget)

        # 下载按钮
        self.buttonsLayout = QHBoxLayout()
        self.buttonsLayout.setSpacing(12)

        self.downloadVideoBtn = PrimaryPushButton("下载无水印视频", self.downloadContainer)
        self.downloadVideoBtn.setIcon(FluentIcon.DOWNLOAD)
        self.downloadVideoBtn.clicked.connect(self.onDownloadVideoClicked)

        self.downloadAudioBtn = ProgressAudioButton("下载原声", self.downloadContainer)
        self.downloadAudioBtn.setIcon(FluentIcon.DOWNLOAD)
        self.downloadAudioBtn.clicked.connect(self.onDownloadAudioClicked)

        self.buttonsLayout.addWidget(self.downloadVideoBtn)
        self.buttonsLayout.addWidget(self.downloadAudioBtn)

        self.downloadLayout.addLayout(self.buttonsLayout)
        self.detailsLayout.addWidget(self.downloadContainer)

        # 添加弹性空间
        self.detailsLayout.addStretch()

        # 将组件添加到主布局
        self.mainLayout.addWidget(self.videoCoverLabel)
        self.mainLayout.addWidget(self.detailsWidget, 1)

        # 初始化图片加载器列表
        self._image_loaders = []

        # 设置样式
        self.setQss()

    def setQss(self):
        """设置样式和对象名称"""
        # 设置对象名称
        self.titleLabel.setObjectName("videoTitle")
        self.platformBadge.setObjectName("platformBadge")
        self.descriptionLabel.setObjectName("videoDescription")
        self.authorNameLabel.setObjectName("authorName")
        self.fansLabel.setObjectName("fansCount")
        self.signatureLabel.setObjectName("userSignature")

        # 统计项目对象名称
        self.heartStatWidget.setObjectName("redStat")
        self.heartCountLabel.setObjectName("statCount")
        self.heartTextLabel.setObjectName("statLabel")

        self.commentStatWidget.setObjectName("blueStat")
        self.commentCountLabel.setObjectName("statCount")
        self.commentTextLabel.setObjectName("statLabel")

        self.shareStatWidget.setObjectName("greenStat")
        self.shareCountLabel.setObjectName("statCount")
        self.shareTextLabel.setObjectName("statLabel")

        self.collectStatWidget.setObjectName("yellowStat")
        self.collectCountLabel.setObjectName("statCount")
        self.collectTextLabel.setObjectName("statLabel")

        # 音乐信息对象名称
        self.musicWidget.setObjectName("musicInfo")
        self.musicLabel.setObjectName("musicLabel")
        self.musicAuthorLabel.setObjectName("musicAuthor")

        # 发布时间信息对象名称
        self.publishTimeWidget.setObjectName("publishTimeInfo")
        self.timeLabel.setObjectName("timeLabel")
        self.publishTimeValueLabel.setObjectName("publishTimeValue")

        # 下载按钮对象名称
        self.downloadVideoBtn.setObjectName("downloadVideoBtn")
        self.downloadAudioBtn.setObjectName("downloadAudioBtn")

        # 应用样式表
        setCustomStyleSheetFromFile(self.downloadVideoBtn, 'video_info_card')
        setCustomStyleSheetFromFile(self.downloadAudioBtn, 'video_info_card')

    def _loadTestCover(self):
        """延迟加载测试封面图片"""
        cover_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "cover.jpeg")
        if os.path.exists(cover_path):
            self.videoCoverLabel.setImage(cover_path)

    def update_douyin_data(self, video_data):
        """更新视频数据"""
        if not video_data:
            return
        # 更新标题
        title = video_data.get('description', video_data.get('caption', '-'))
        self.titleLabel.setText(title)

        # 更新描述
        description = video_data.get('video_desc', video_data.get('description', '-'))
        self.descriptionLabel.setText(description)

        # 更新平台标签
        platform_name = video_data.get('platform_name', video_data.get('platform', '-'))
        self.platformBadge.setText(platform_name)

        # 更新作者信息
        author_name = video_data.get('author_name', '-')
        self.authorNameLabel.setText(author_name)

        # 更新粉丝数
        fans_count = video_data.get('author_fans', 0)
        if fans_count > 0:
            self.fansLabel.setText(f"粉丝：{self._format_number(fans_count)}")
        else:
            self.fansLabel.setText("粉丝：-")
        self.fansLabel.setVisible(True)

        # 更新签名
        signature = video_data.get('author_signature', '-')
        self.signatureLabel.setText(signature)

        # 更新统计数据
        heart_count = video_data.get('video_heart', video_data.get('like_count', 0))
        self.heartCountLabel.setText(self._format_number(heart_count))

        comment_count = video_data.get('video_comment', video_data.get('reply_count', 0))
        self.commentCountLabel.setText(self._format_number(comment_count))

        share_count = video_data.get('video_share', 0)
        self.shareCountLabel.setText(self._format_number(share_count))

        collect_count = video_data.get('video_collect', video_data.get('favorite_count', 0))
        self.collectCountLabel.setText(self._format_number(collect_count))

        # 隐藏投币组件（抖音没有投币功能）
        self.coinStatWidget.setVisible(False)

        # 更新音乐信息
        music_author = video_data.get('music_author', video_data.get('music_title', '-'))
        if music_author and music_author != '-':
            self.musicAuthorLabel.setText(music_author)
            self.musicWidget.show()
        else:
            self.musicWidget.hide()

        # 更新发布时间
        publish_time = video_data.get('update_time', '-')
        if publish_time and publish_time != '-':
            publish_time = datetime.fromtimestamp(publish_time).strftime('%Y年%m月%d日%H：%M')
            self.publishTimeValueLabel.setText(publish_time)
            self.publishTimeWidget.show()
        else:
            self.publishTimeWidget.hide()

        # 更新标签（仅抖音有标签）
        tags = video_data.get('tags', [])
        if tags and video_data.get('platform') == '抖音':
            # 清除现有标签
            self._clear_tags()

            # 添加新标签
            for tag in tags:
                tag_btn = PillPushButton(tag, self.tagsContainer)
                tag_btn.setCheckable(False)
                self.tagsFlowLayout.addWidget(tag_btn)

            self.tagsContainer.show()
        else:
            self.tagsContainer.hide()

        # 更新封面图片
        cover_url = video_data.get('video_cover') or video_data.get('video_dynamic_cover')
        if cover_url:
            self.load_network_image(cover_url, 'cover')

        # 更新头像
        avatar_url = video_data.get('author_avatar')
        if avatar_url:
            self.load_network_image(avatar_url, 'avatar')
        self.videoInfoDict = video_data

        signalBus.hideUnsureSignal.emit()

    def update_bilibili_video(self, video_data):
        """更新视频数据"""
        if not video_data:
            return
        # 更新标题
        title = video_data.get('title', '-')
        self.titleLabel.setText(title)

        # 更新描述
        description = video_data.get('desc', '-')
        self.descriptionLabel.setText(description)

        # 更新平台标签
        platform_name = video_data.get('platform', '-')
        self.platformBadge.setText(platform_name)

        # 更新作者信息
        author_name = video_data['owner'].get('name', '-')
        self.authorNameLabel.setText(author_name)

        # 更新粉丝数
        self.fansLabel.setVisible(False)

        # 更新签名
        self.signatureLabel.setText("UP主")

        # 更新统计数据
        heart_count = video_data['stat'].get('like', 0)
        self.heartCountLabel.setText(self._format_number(heart_count))

        comment_count = video_data['stat'].get('reply', 0)
        self.commentCountLabel.setText(self._format_number(comment_count))

        share_count = video_data['stat'].get('share', 0)
        self.shareCountLabel.setText(self._format_number(share_count))

        collect_count = video_data['stat'].get('favorite', 0)
        self.collectCountLabel.setText(self._format_number(collect_count))

        # 更新投币数据（仅B站显示）
        coin_count = video_data['stat'].get('coin', 0)
        self.coinCountLabel.setText(self._format_number(coin_count))
        self.coinStatWidget.setVisible(True)

        # 更新音乐信息
        music_author = video_data.get('music_author', video_data.get('music_title', '-'))
        if music_author and music_author != '-':
            self.musicAuthorLabel.setText(music_author)
            self.musicWidget.show()
        else:
            self.musicWidget.hide()

        # 更新发布时间
        publish_time = video_data.get('pubdate', '-')
        if publish_time and publish_time != '-':
            publish_time = datetime.fromtimestamp(publish_time).strftime('%Y年%m月%d日%H：%M')
            self.publishTimeValueLabel.setText(publish_time)
            self.publishTimeWidget.show()
        else:
            self.publishTimeWidget.hide()

        self.tagsContainer.hide()

        # 更新封面图片
        bili_login = BilibiliLogin()
        is_logged_in = bili_login.load_cookies() and bili_login.get_user_info() is not None
        
        if is_logged_in:
            cover_url = video_data.get('pic')  # 登录状态使用pic字段
        else:
            cover_url = video_data.get('cover')  # 未登录状态使用cover字段
        
        if cover_url:
            self.load_network_image(cover_url, 'cover')

        # 更新头像
        avatar_url = video_data['owner'].get('face')
        if avatar_url:
            self.load_network_image(avatar_url, 'avatar')
        self.videoInfoDict = video_data

        signalBus.hideUnsureSignal.emit()

    def _format_number(self, num):
        """格式化数字显示"""
        if num >= 100000000:  # 1亿
            return f"{num / 100000000:.1f}亿"
        elif num >= 10000:  # 1万
            return f"{num / 10000:.1f}万"
        elif num >= 1000:  # 1千
            return f"{num / 1000:.1f}千"
        else:
            return str(num)

    def _clear_tags(self):
        """清除所有标签"""
        while self.tagsFlowLayout.count():
            widget = self.tagsFlowLayout.takeAt(0)
            if widget:
                widget.deleteLater()

    def load_network_image(self, url, image_type):
        """异步加载网络图片"""
        if not url:
            return

        loader = ImageLoaderThread(url, image_type)
        loader.imageLoaded.connect(self.on_image_loaded)
        loader.loadFailed.connect(self.on_image_load_failed)
        loader.start()

        # 保存线程引用防止被垃圾回收
        self._image_loaders.append(loader)

    def on_image_loaded(self, pixmap, image_type):
        """图片加载完成回调"""
        if image_type == 'cover':
            # 设置封面图片
            scaled_pixmap = pixmap.scaled(
                300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.videoCoverLabel.setPixmap(scaled_pixmap)
        elif image_type == 'avatar':
            # 设置头像图片
            scaled_image = pixmap.toImage().scaled(
                40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.avatar.setImage(scaled_image)

    def on_image_load_failed(self, image_type):
        """图片加载失败回调"""
        InfoBar.error(
            title="加载失败",
            content=f"{image_type} 图片加载失败",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self.window()
        )

    def cleanup_image_loaders(self):
        """清理图片加载线程"""
        for loader in self._image_loaders:
            if loader.isRunning():
                loader.stop()
        self._image_loaders.clear()

    def onDownloadVideoClicked(self):
        """处理下载视频按钮点击事件"""
        if not self.videoInfoDict:
            return
        
        # 检查是否为B站视频
        if self.videoInfoDict.get('platform') == 'B站':
            # B站视频，直接显示质量选择对话框
            self.window().bilibili_quality_dialog = BilibiliQualityDialog(self.videoInfoDict, self.window())
            self.window().bilibili_quality_dialog.show()
        else:
            # 其他平台视频，直接显示质量选择对话框
            self.window().video_quality_dialog = VideoQualityDialog(self.videoInfoDict, self.window())
            self.window().video_quality_dialog.show()

    def startDownload(self, quality_data):
        """开始下载视频"""
        if not quality_data or 'url' not in quality_data:
            InfoBar.error(
                title="下载失败",
                content="下载链接无效",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self.window()
            )
            return

        # 如果已有下载任务在进行，先停止
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()

        # 禁用下载按钮
        self.downloadVideoBtn.setEnabled(False)

        # 显示进度条
        self.progressWidget.show()
        self.progressBar.setValue(0)
        self.progressPercent.setText("0%")

        # 获取分辨率
        resolution = quality_data.get('resolution', 'unknown')

        # 创建下载线程（使用时间戳+分辨率的文件名）
        self.download_thread = VideoDownloadThread(
            download_url=quality_data['url'],
            resolution=resolution
        )

        self.download_thread.progress.connect(self.updateProgress)
        self.download_thread.finished.connect(self.onDownloadFinished)
        self.download_thread.error.connect(self.onDownloadError)

        # 开始下载
        self.download_thread.start()
    
    def closeEvent(self, event):
        """组件关闭时清理资源"""
        # 清理图片加载线程
        self.cleanup_image_loaders()
        
        # 清理下载线程
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_thread.deleteLater()
            self.download_thread = None
        
        super().closeEvent(event)

    def updateProgress(self, progress):
        """更新下载进度"""
        self.progressBar.setValue(progress)
        self.progressPercent.setText(f"{progress}%")

    def onDownloadFinished(self, file_path):
        """下载完成处理"""
        # 重置进度条
        self.progressBar.setValue(0)
        self.progressPercent.setText("0%")
        self.progressWidget.hide()

        # 启用下载按钮
        self.downloadVideoBtn.setEnabled(True)

        # 清理线程引用
        if hasattr(self, 'download_thread') and self.download_thread:
            # 断开信号连接
            try:
                self.download_thread.progress.disconnect()
                self.download_thread.finished.disconnect()
                self.download_thread.error.disconnect()
            except:
                pass
            # 确保线程已经完成再删除
            if not self.download_thread.isRunning():
                self.download_thread.deleteLater()
            else:
                # 如果线程仍在运行，等待完成后再删除
                self.download_thread.finished.connect(lambda: self.download_thread.deleteLater())
            self.download_thread = None

        InfoBar.success(
            title="下载完成",
            content=f"视频已保存到默认目录",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self.window()
        )

    def onDownloadError(self, error_message):
        """下载错误处理"""
        # 重置进度条
        self.progressBar.setValue(0)
        self.progressPercent.setText("0%")
        self.progressWidget.hide()

        # 启用下载按钮
        self.downloadVideoBtn.setEnabled(True)

        # 清理线程引用
        if hasattr(self, 'download_thread') and self.download_thread:
            # 断开信号连接
            try:
                self.download_thread.progress.disconnect()
                self.download_thread.finished.disconnect()
                self.download_thread.error.disconnect()
            except:
                pass
            # 确保线程已经完成再删除
            if not self.download_thread.isRunning():
                self.download_thread.deleteLater()
            else:
                # 如果线程仍在运行，等待完成后再删除
                self.download_thread.finished.connect(lambda: self.download_thread.deleteLater())
            self.download_thread = None

        InfoBar.error(
            title="下载失败",
            content=error_message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self.window()
        )

    def startAudioDownload(self, video_info):
        """开始下载音频"""
        if not video_info:
            InfoBar.error(
                title="音频下载失败",
                content="视频信息无效",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
            return

        # 如果已有音频下载线程在运行，先停止
        if self.audio_download_thread and self.audio_download_thread.isRunning():
            self.audio_download_thread.stop()

        # 禁用音频下载按钮
        self.downloadAudioBtn.setEnabled(False)

        # 检查平台类型和音频格式
        platform = video_info.get('platform', '')
        play_info = video_info.get('play_info', {})
        
        if platform == 'Bilibili' or 'dash' in play_info:
            # Bilibili平台或DASH格式，使用BilibiliDownloadThread
            if 'durl' in play_info:
                # 传统格式，无法单独提取音频
                InfoBar.error(
                    title="音频下载失败",
                    content="该视频格式不支持单独下载音频",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.window()
                )
                self.downloadAudioBtn.setEnabled(True)
                return
            
            if 'dash' not in play_info:
                InfoBar.error(
                    title="音频下载失败",
                    content="未找到音频流信息",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.window()
                )
                self.downloadAudioBtn.setEnabled(True)
                return

            # 使用BilibiliDownloadThread来下载音频，确保有正确的认证信息
            audio_quality_data = {
                'type': 'audio_only',
                'quality_desc': '音频'
            }
            
            self.audio_download_thread = BilibiliDownloadThread(
                video_info=video_info,
                quality_data=audio_quality_data
            )
        else:
            # 其他平台（如抖音），使用AudioDownloadThread
            audio_url = video_info.get('audio_url') or video_info.get('music_url')
            if not audio_url:
                InfoBar.error(
                    title="音频下载失败",
                    content="未找到音频下载链接",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.window()
                )
                self.downloadAudioBtn.setEnabled(True)
                return

            self.audio_download_thread = AudioDownloadThread(
                download_url=audio_url
            )

        self.audio_download_thread.finished.connect(self.onAudioDownloadFinished)
        self.audio_download_thread.error.connect(self.onAudioDownloadError)
        self.audio_download_thread.progress.connect(self.updateAudioProgress)

        self.audio_download_thread.start()

    def updateAudioProgress(self, progress):
        """更新音频下载进度"""
        self.downloadAudioBtn.setProgress(progress)

    def onAudioDownloadFinished(self, file_path):
        """音频下载完成"""
        # 清除进度显示
        self.downloadAudioBtn.clearProgress()

        # 启用音频下载按钮
        self.downloadAudioBtn.setEnabled(True)

        InfoBar.success(
            title="音频下载完成",
            content=f"文件已保存至默认目录",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )

    def onAudioDownloadError(self, error_message):
        """音频下载错误处理"""
        # 清除进度显示
        self.downloadAudioBtn.clearProgress()

        # 启用音频下载按钮
        self.downloadAudioBtn.setEnabled(True)

        InfoBar.error(
            title="音频下载失败",
            content=error_message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )

    def onDownloadAudioClicked(self):
        """音频下载按钮点击事件"""
        if not self.videoInfoDict:
            InfoBar.error(
                title="音频下载失败",
                content="请先获取视频信息",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
            return

        # 发送音频下载信号
        signalBus.startAudioDownloadSig.emit(self.videoInfoDict)
    
    def startBilibiliDownload(self, quality_data):
        """开始B站视频下载"""
        if not quality_data:
            InfoBar.error(
                title="下载失败",
                content="下载数据无效",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self.window()
            )
            return
        
        # 如果已有下载任务在进行，先停止
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
        
        # 禁用下载按钮
        self.downloadVideoBtn.setEnabled(False)
        
        # 显示进度条
        self.progressWidget.show()
        self.progressBar.setValue(0)
        self.progressPercent.setText("0%")
        
        # 创建B站下载线程
        self.download_thread = BilibiliDownloadThread(
            quality_data=quality_data,
            video_info=self.videoInfoDict
        )
        
        # 连接信号
        self.download_thread.progress.connect(self.updateProgress)
        self.download_thread.finished.connect(self.onDownloadFinished)
        self.download_thread.error.connect(self.onDownloadError)
        
        # 开始下载
        self.download_thread.start()
