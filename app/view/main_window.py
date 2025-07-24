# coding:utf-8
from PyQt5.QtCore import Qt, QRect, QUrl, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QIcon, QPainter, QImage, QBrush, QColor, QFont, QDesktopServices, QKeySequence
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QShortcut, QSystemTrayIcon

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, NavigationWidget, MessageBox,
                            isDarkTheme, setTheme, Theme, qrouter, qconfig, InfoBar, InfoBarPosition,
                            Action, SystemTrayMenu)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow, TitleBar

from .home_interface import HomeInterface
from .setting_interface import SettingInterface
from ..common.style_sheet import setStyleSheet
from ..common import resource_rc
from ..common.config import config
from ..common.signal_bus import signalBus
from ..common.vidflowicon import VidFlowIcon
from ..components.IndeterminateProgressDialog import CustomMessageBox
from ..components.SlidingStackedWidget import SlidingStackedWidget
from ..components.video_quality_dialog import VideoQualityDialog
from ..components.bilibili_quality_dialog import BilibiliQualityDialog


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        # leave some space for title bar
        self.hBoxLayout.setContentsMargins(0, 32, 0, 0)


class AvatarWidget(NavigationWidget):
    """ Avatar widget """

    def __init__(self, parent=None):
        super().__init__(isSelectable=False, parent=parent)
        self.avatar = QImage(':images/mark.jpg').scaled(
            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)

        # draw background
        if self.isEnter:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # draw avatar
        painter.setBrush(QBrush(self.avatar))
        painter.translate(8, 6)
        painter.drawEllipse(0, 0, 24, 24)
        painter.translate(-8, -6)

        if not self.isCompacted:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            font = QFont('Segoe UI')
            font.setPixelSize(14)
            painter.setFont(font)
            painter.drawText(QRect(44, 0, 255, 36), Qt.AlignVCenter, '怪兽马尔克')


class CustomTitleBar(TitleBar):
    """ Title bar with icon and title """

    def __init__(self, parent):
        super().__init__(parent)
        # add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        self.hBoxLayout.insertSpacing(0, 10)
        self.hBoxLayout.insertWidget(1, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.window().windowIconChanged.connect(self.setIcon)

        # add title label
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))


class MainWindow(FramelessWindow):

    def __init__(self):
        super().__init__()
        self.setTitleBar(CustomTitleBar(self))
        # setTheme(Theme.DARK)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.navigationInterface = NavigationInterface(self, showReturnButton=True)
        self.stackWidget = SlidingStackedWidget(self)

        self.stackWidget.setOrientation(Qt.Vertical)
        self.stackWidget.setEasing(QEasingCurve.InOutCirc)

        # 初始化对话框
        self.video_quality_dialog = None
        self.bilibili_quality_dialog = None

        # 初始化系统托盘
        self.initSystemTray()

        # create sub interface
        self.searchInterface = HomeInterface(self)
        self.settingInterface = SettingInterface(self)

        # initialize layout
        self.initLayout()

        # add items to navigation interface
        self.initNavigation()

        self.initWindow()

        self.__connectSignalToSlot()

    def initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

        self.titleBar.raise_()

    def initNavigation(self):
        self.addSubInterface(self.searchInterface, FIF.HOME, 0, '主页')

        self.navigationInterface.addSeparator()

        # add navigation items to scroll area

        # add custom widget to bottom
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=AvatarWidget(),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM
        )

        self.addSubInterface(self.settingInterface, FIF.SETTING, 1, '设置', NavigationItemPosition.BOTTOM)

        # !IMPORTANT: don't forget to set the default route key
        qrouter.setDefaultRouteKey(self.stackWidget, self.searchInterface.objectName())

        # set the maximum width
        self.navigationInterface.setExpandWidth(250)

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.stackWidget.setCurrentIndex(0)

    def initWindow(self):
        self.resize(900, 700)
        self.setMinimumWidth(850)
        self.setWindowIcon(VidFlowIcon.LOGO.icon())
        self.setWindowTitle('VidFlow Desktop')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.setQss()

    def initSystemTray(self):
        """初始化系统托盘"""
        # 检查系统是否支持托盘
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        # 创建托盘图标
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(VidFlowIcon.LOGO.icon())
        self.trayIcon.setToolTip('VidFlow Desktop')

        # 创建托盘菜单（使用qfluentwidgets的SystemTrayMenu）
        self.trayMenu = SystemTrayMenu(parent=self)

        # 添加菜单项
        self.trayMenu.addActions([
            Action(FIF.HOME, '显示主界面', triggered=self.showMainWindow),
            Action(FIF.SETTING, '设置', triggered=self.showSettings),
            Action(FIF.FOLDER, '打开下载目录', triggered=self.openDownloadFolder),
            Action(FIF.INFO, '关于', triggered=self.showAbout),
            Action(FIF.CLOSE, '退出', triggered=self.quitApplication),
        ])

        # 设置托盘菜单
        self.trayIcon.setContextMenu(self.trayMenu)

        # 连接托盘图标点击事件
        self.trayIcon.activated.connect(self.onTrayIconActivated)

        # 显示托盘图标
        self.trayIcon.show()

    def onTrayIconActivated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.showMainWindow()

    def showMainWindow(self):
        """显示主界面"""
        self.show()
        self.raise_()
        self.activateWindow()

    def showSettings(self):
        """显示设置界面"""
        self.showMainWindow()
        # 切换到设置界面
        self.switchTo(1)

    def openDownloadFolder(self):
        """打开下载目录"""
        download_path = config.get(config.downloadFolder)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(download_path)))

    def showAbout(self):
        """显示关于对话框"""
        w = MessageBox(
            '关于 VidFlow Desktop',
            '一个基于 PyQt5 和 qfluentwidgets 开发的视频下载工具\n\n'
            '支持抖音、B站等平台的视频下载\n'
            '作者：怪兽马尔克\n'
            '版本：1.0.0',
            self
        )
        w.yesButton.setText('确定')
        w.cancelButton.hide()
        w.exec()

    def quitApplication(self):
        """退出应用程序"""
        if self.trayIcon:
            self.trayIcon.hide()
        QApplication.quit()

    def __connectSignalToSlot(self):
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)
        signalBus.showUnsureSignal.connect(self.showDialog)
        signalBus.hideUnsureSignal.connect(self.hideDialog)

        # 主题变化信号连接
        qconfig.themeChanged.connect(self.__onThemeChanged)

        # 保留必要的信号连接
        signalBus.videoQualitySelectedSig.connect(self.onVideoQualitySelected)
        signalBus.bilibiliQualitySelectedSig.connect(self.onBilibiliQualitySelected)

    def addSubInterface(self, interface, icon, index, text: str, position=NavigationItemPosition.TOP):
        """ add sub interface """
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(index),
            position=position,
            tooltip=text
        )

    def setQss(self):
        self.setObjectName("mainWindow")
        setStyleSheet(self, 'main_window')

    def switchTo(self, index):
        self.stackWidget.setCurrentIndex(index)

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())
        qrouter.push(self.stackWidget, widget.objectName())

    def showMessageBox(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://ifdian.net/a/markingchen"))

    def showDialog(self):
        self.custom_w = CustomMessageBox(self)
        self.custom_w.show()

    def hideDialog(self):
        if self.custom_w:
            self.custom_w.reject()

    def __onThemeChanged(self):
        """主题变化时重新应用样式"""
        # 重新应用主窗口样式
        self.setQss()

        # 重新应用所有子界面的样式
        for i in range(self.stackWidget.count()):
            widget = self.stackWidget.widget(i)
            if hasattr(widget, 'setQss'):
                widget.setQss()

    def onVideoQualitySelected(self, quality_data):
        """处理用户选择的视频质量"""
        # 发送开始下载信号
        signalBus.startVideoDownloadSig.emit(quality_data)

        # 清理对话框引用
        self.video_quality_dialog = None

    def onBilibiliQualitySelected(self, quality_data):
        """处理用户选择的B站视频质量"""
        # 发送开始B站视频下载信号
        signalBus.startBilibiliDownloadSig.emit(quality_data)

        # 清理对话框引用
        self.bilibili_quality_dialog = None

    def closeEvent(self, event):
        """重写关闭事件，实现最小化到托盘"""
        if config.get(config.minimizeToTray) and self.trayIcon and self.trayIcon.isVisible():
            # 最小化到托盘
            self.hide()
            self.trayIcon.showMessage(
                "VidFlow Desktop",
                "应用程序已最小化到托盘",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
        else:
            # 直接退出
            self.quitApplication()
            event.accept()

    def resizeEvent(self, e):
        self.titleBar.move(46, 0)
        self.titleBar.resize(self.width() - 46, self.titleBar.height())
