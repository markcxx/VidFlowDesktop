import sys
import os
from typing import Dict

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from qfluentwidgets import (
    LineEdit, ElevatedCardWidget, BodyLabel, CaptionLabel,
    InfoBar, InfoBarPosition, FluentIcon, PrimaryPushButton, ScrollArea
)

from ..common.signal_bus import signalBus
from ..common.style_sheet import setStyleSheet, setCustomStyleSheetFromFile
from ..common import resource_rc
from ..common.vidflowicon import VidFlowIcon
from ..common.threadManager import ParsingVideoThread
from ..components.coloricon_widget import ColorIconWidget
from ..components.gradient_Label import GradientLabel
from ..components.videoInfo_card import VideoInfoCard


class HomeHeaderWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.vboxLayout = QVBoxLayout(self)
        self.vboxLayout.setAlignment(Qt.AlignCenter)
        self.vboxLayout.setSpacing(8)

        self.badge_widget = QWidget(self)
        self.badge_widget.setObjectName("badgeWidget")
        self.badge_widget.setFixedHeight(40)
        self.badge_widget.setMinimumWidth(200)

        self.badge_layout = QHBoxLayout(self.badge_widget)
        self.badge_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.badge_layout.setSpacing(8)
        self.badge_layout.setContentsMargins(10, 0, 10, 0)

        self.iconWidget = ColorIconWidget(VidFlowIcon.STAR_PLUS, self.badge_widget)
        self.iconWidget.setColor(QColor(59, 130, 246))
        self.iconWidget.setFixedSize(32, 32)

        self.badgeLabel = CaptionLabel("多平台视频下载工具VidFlow", self.badge_widget)
        self.badgeLabel.setTextColor(QColor(59, 130, 246), QColor(59, 130, 246))
        self.badgeLabel.setFont(QFont("Microsoft YaHei", 12, QFont.Medium))

        self.badge_layout.addWidget(self.iconWidget)
        self.badge_layout.addWidget(self.badgeLabel)

        self.titleLabel = GradientLabel("视频解析下载", self)
        # self.titleLabel.setTextColor(QColor(90, 80, 235), QColor(90, 80, 235))
        self.titleLabel.setFont(QFont("Microsoft YaHei", 25, QFont.Bold))

        self.subtitleLabel = BodyLabel("支持主流平台无水印视频下载，一键获取高清原片和音频文件", self)
        self.subtitleLabel.setAlignment(Qt.AlignCenter)
        self.subtitleLabel.setTextColor(QColor(147, 155, 166), QColor(147, 155, 166))
        self.subtitleLabel.setFont(QFont("Microsoft YaHei", 12, QFont.Medium))

        self.vboxLayout.addWidget(self.badge_widget, 0, Qt.AlignCenter)
        self.vboxLayout.addWidget(self.titleLabel, 0, Qt.AlignCenter)
        self.vboxLayout.addWidget(self.subtitleLabel, 0, Qt.AlignCenter)

        self.setQss()

    def setQss(self):
        self.setObjectName("HomeHeaderWidget")
        self.badge_widget.setObjectName("badgewidget")
        self.badgeLabel.setObjectName("badgeLabel")
        setStyleSheet(self, 'homeheader_widget')


class InputCard(ElevatedCardWidget):
    getData = pyqtSignal(dict)
    getDataError = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parsing_thread = None
        self.setMinimumHeight(100)

        self.hboxLayout = QHBoxLayout(self)
        self.hboxLayout.setAlignment(Qt.AlignVCenter)
        self.hboxLayout.setSpacing(16)
        self.hboxLayout.setContentsMargins(24, 20, 24, 20)

        # search LineEdit
        self.lineEdit = LineEdit(self)
        self.lineEdit.setClearButtonEnabled(True)
        self.lineEdit.setPlaceholderText("粘贴视频链接...")
        self.lineEdit.setFixedHeight(48)

        # search button
        self.searchButton = PrimaryPushButton("解析视频", self)
        self.searchButton.setIcon(FluentIcon.PLAY)
        self.searchButton.setDisabled(True)
        self.searchButton.setFixedSize(120, 48)

        self.hboxLayout.addWidget(self.lineEdit, 1)
        self.hboxLayout.addWidget(self.searchButton, 0)
        
        # 连接文本变化信号
        self.lineEdit.textChanged.connect(self.onTextChanged)
        self.searchButton.clicked.connect(self.startParsingThread)
        
        self.setQss()
    
    def onTextChanged(self, text):
        """当lineEdit文本变化时调用，控制searchButton的启用状态"""
        self.searchButton.setEnabled(bool(text.strip()))

    def startParsingThread(self):
        self.parsing_thread = ParsingVideoThread(self.lineEdit.text())
        self.parsing_thread.finished.connect(lambda data: self.getData.emit(data))
        self.parsing_thread.error.connect(lambda info: self.getDataError.emit(info))
        self.parsing_thread.start()
        self.lineEdit.setEnabled(False)
        self.searchButton.setEnabled(False)
        signalBus.showUnsureSignal.emit()
    
    def setQss(self):
        
        self.lineEdit.setObjectName("SearchLineEdit")
        self.searchButton.setObjectName("SearchButton")

        setStyleSheet(self, 'input_card')
        
        # 使用外部 QSS 文件设置自定义样式
        setCustomStyleSheetFromFile(self.lineEdit, 'input_card')
        setCustomStyleSheetFromFile(self.searchButton, 'input_card')


class HomeInterface(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 40, 0, 0)

        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)

        self.headerWidget = HomeHeaderWidget(self.scrollWidget)
        self.inputCard = InputCard(self.scrollWidget)
        self.videoInfoCard = VideoInfoCard(self.scrollWidget)
        self.videoInfoCard.setVisible(False)

        self.expandLayout.addWidget(self.headerWidget)
        self.expandLayout.addWidget(self.inputCard)
        self.expandLayout.addWidget(self.videoInfoCard)
        self.expandLayout.addStretch()

        self.expandLayout.setContentsMargins(10, 10, 20, 0)
        self.setWidget(self.scrollWidget)
        self.setQss()

        self.inputCard.getData.connect(self.setVideoInfo)
        self.inputCard.getDataError.connect(self.updataError)

    def setQss(self):
        self.setObjectName("HomeInterface")
        self.scrollWidget.setObjectName("scrollWidget")
        setStyleSheet(self, 'home_interface')

    def setVideoInfo(self, data):
        if data.get('platform') == '抖音':
            self.videoInfoCard.update_douyin_data(data)
        elif data.get('platform') == 'B站':
            self.videoInfoCard.update_bilibili_video(data)
        self.videoInfoCard.setVisible(True)
        self.inputCard.lineEdit.setEnabled(True)
        self.inputCard.searchButton.setEnabled(True)

        InfoBar.success(
            title='解析成功',
            content='视频信息已获取，可以开始下载了',
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )

    def updataError(self, info):
        self.inputCard.lineEdit.setEnabled(True)
        self.inputCard.searchButton.setEnabled(True)
        signalBus.hideUnsureSignal.emit()
        InfoBar.error(
            title='解析失败',
            content=info,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
