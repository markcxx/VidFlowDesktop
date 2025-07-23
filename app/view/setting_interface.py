# coding:utf-8
import os
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QStackedWidget, QFileDialog

from qfluentwidgets import (
    ScrollArea, SegmentedWidget, SettingCardGroup, SwitchSettingCard, 
    OptionsSettingCard, PushSettingCard, HyperlinkCard, PrimaryPushSettingCard,
    ComboBoxSettingCard, ExpandLayout, CustomColorSettingCard, RangeSettingCard,
    setTheme, setThemeColor, FluentIcon as FIF, InfoBar, TitleLabel, qconfig, InfoBarPosition
)

from ..common.vidflowicon import VidFlowIcon
from ..components.bili_login_dialog import BiliLoginDialog
from ..common.bilibili_login import BilibiliLogin
from ..common.config import config, LOGIN_FILE_PATH
from ..common.signal_bus import signalBus
from ..common.style_sheet import setStyleSheet
from ..common.bilibili_login import BilibiliLogin


class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        
        # 设置标题
        self.settingLabel = TitleLabel(self.tr("设置"), self)
        
        # 创建分段控件
        self.pivot = SegmentedWidget(self.scrollWidget)
        
        # 创建堆叠窗口
        self.stackedWidget = QStackedWidget(self.scrollWidget)
        
        # 创建各个子页面
        self.personalPage = PersonalizationPage(self.scrollWidget)
        self.loginPage = LoginManagementPage(self.scrollWidget)
        self.downloadPage = DownloadSettingsPage(self.scrollWidget)
        self.otherPage = OtherSettingsPage(self.scrollWidget)
        self.aboutPage = AboutAuthorPage(self.scrollWidget)
        
        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')
        
        # 初始化分段控件
        self.pivot.addItem("personal", self.tr("个性化"), icon=FIF.PALETTE)
        self.pivot.addItem("login", self.tr("登录管理"), icon=FIF.PEOPLE)
        self.pivot.addItem("download", self.tr("下载设置"), icon=FIF.DOWNLOAD)
        self.pivot.addItem("other", self.tr("其他设置"), icon=FIF.SETTING)
        self.pivot.addItem("about", self.tr("关于作者"), icon=FIF.INFO)
        self.pivot.setCurrentItem("personal")
        
        # 添加页面到堆叠窗口
        self.stackedWidget.addWidget(self.personalPage)
        self.stackedWidget.addWidget(self.loginPage)
        self.stackedWidget.addWidget(self.downloadPage)
        self.stackedWidget.addWidget(self.otherPage)
        self.stackedWidget.addWidget(self.aboutPage)
        
        # 设置样式
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        self.setQss()
    
    def setQss(self):
        """设置样式表"""
        setStyleSheet(self, 'setting_interface')

    def __initLayout(self):
        self.settingLabel.move(36, 30)
        
        self.vBoxLayout.setContentsMargins(36, 10, 36, 0)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)

    def __connectSignalToSlot(self):
        self.pivot.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k)))


class PersonalizationPage(QWidget):
    """ 个性化页面 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("personal")
        self.expandLayout = ExpandLayout(self)
        
        # 主题设置组
        self.themeGroup = SettingCardGroup(self.tr('主题设置'), self)
        
        self.themeCard = OptionsSettingCard(
            qconfig.themeMode,
            FIF.BRUSH,
            self.tr('应用主题'),
            self.tr("更改应用程序的外观"),
            texts=[
                self.tr('浅色'), self.tr('深色'),
                self.tr('跟随系统设置')
            ],
            parent=self.themeGroup
        )
        
        self.themeColorCard = CustomColorSettingCard(
            qconfig.themeColor,
            FIF.PALETTE,
            self.tr('主题色'),
            self.tr('更改应用程序的主题颜色'),
            self.themeGroup
        )
        
        # 界面设置组
        self.interfaceGroup = SettingCardGroup(self.tr('界面设置'), self)
        
        self.zoomCard = OptionsSettingCard(
            config.dpiScale,
            FIF.ZOOM,
            self.tr("界面缩放"),
            self.tr("更改小部件和字体的大小"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("跟随系统设置")
            ],
            parent=self.interfaceGroup
        )
        
        self.languageCard = ComboBoxSettingCard(
            config.language,
            FIF.LANGUAGE,
            self.tr('语言'),
            self.tr('设置界面显示语言'),
            texts=['简体中文', '繁體中文', 'English', self.tr('跟随系统设置')],
            parent=self.interfaceGroup
        )
        
        # 系统设置组
        self.systemGroup = SettingCardGroup(self.tr('系统设置'), self)
        
        self.startupCard = SwitchSettingCard(
            FIF.POWER_BUTTON,
            self.tr('开机自启动'),
            self.tr('开机时自动启动应用程序'),
            config.startupOnBoot,
            self.systemGroup
        )
        
        self.trayCard = SwitchSettingCard(
            FIF.MINIMIZE,
            self.tr('最小化到托盘'),
            self.tr('关闭窗口时最小化到系统托盘'),
            config.minimizeToTray,
            self.systemGroup
        )
        
        self.__initLayout()
        self.__connectSignalToSlot()
    
    def __initLayout(self):
        # 添加卡片到组
        self.themeGroup.addSettingCard(self.themeCard)
        self.themeGroup.addSettingCard(self.themeColorCard)
        
        self.interfaceGroup.addSettingCard(self.zoomCard)
        self.interfaceGroup.addSettingCard(self.languageCard)
        
        self.systemGroup.addSettingCard(self.startupCard)
        self.systemGroup.addSettingCard(self.trayCard)
        
        # 添加组到布局
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(0, 0, 0, 0)
        self.expandLayout.addWidget(self.themeGroup)
        self.expandLayout.addWidget(self.interfaceGroup)
        self.expandLayout.addWidget(self.systemGroup)
    
    def __connectSignalToSlot(self):
        qconfig.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        qconfig.appRestartSig.connect(self.__showRestartTooltip)
        self.themeCard.optionChanged.connect(lambda: setTheme(qconfig.get(qconfig.themeMode)))
        self.zoomCard.optionChanged.connect(self.__showRestartTooltip)
    
    def __showRestartTooltip(self):
        """ 显示重启提示 """
        InfoBar.success(
            self.tr('更新成功'),
            self.tr('配置在重启后生效'),
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
            parent=self.window()
        )


class LoginManagementPage(QWidget):
    """ 登录管理页面 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("login")
        self.expandLayout = ExpandLayout(self)
        
        # 账号管理组
        self.accountGroup = SettingCardGroup(self.tr('账号管理'), self)
        
        self.biliLoginCard = PushSettingCard(
            self.tr('登录'),
            VidFlowIcon.BILIBILI,
            self.tr('B站账号'),
            self.tr('登录B站账号以获取更多功能'),
            self.accountGroup
        )
        
        self.douyinLoginCard = PushSettingCard(
            self.tr('登录'),
            VidFlowIcon.DOUYIN,
            self.tr('抖音账号'),
            self.tr('登录抖音账号以获取更多功能'),
            self.accountGroup
        )
        
        # 初始化B站登录状态
        self._checkBiliLoginStatus()
        
        self.__initLayout()
        self.__connectSignalToSlot()
    
    def __initLayout(self):
        self.accountGroup.addSettingCard(self.biliLoginCard)
        self.accountGroup.addSettingCard(self.douyinLoginCard)
        
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(0, 0, 0, 0)
        self.expandLayout.addWidget(self.accountGroup)
    
    def __connectSignalToSlot(self):
        """连接信号到槽函数"""
        self.biliLoginCard.clicked.connect(self.__onBiliLoginCardClicked)
    
    def __onBiliLoginCardClicked(self):
        """B站登录卡片点击槽函数"""
        # 检查当前登录状态
        if self._isBiliLoggedIn():
            # 已登录，执行退出登录
            self._logoutBili()
        else:
            # 未登录，打开登录对话框
            dialog = BiliLoginDialog(self)
            if dialog.exec_() == dialog.Accepted:
                # 登录成功后更新UI
                self._checkBiliLoginStatus()
    
    def _checkBiliLoginStatus(self):
        """检查B站登录状态并更新UI"""
        try:
            bili_login = BilibiliLogin()
            if bili_login.load_cookies():
                user_info = bili_login.get_user_info()
                if user_info and not user_info.get('isLogin', False) == False:
                    # 已登录状态
                    username = user_info.get('uname', '未知用户')
                    self._updateBiliLoginUI(True, username)
                    return
        except Exception:
            pass
        
        # 未登录状态
        self._updateBiliLoginUI(False)
    
    def _updateBiliLoginUI(self, is_logged_in, username=None):
        """更新B站登录卡片UI"""
        if is_logged_in:
            # 已登录状态
            self.biliLoginCard.setContent(self.tr(f'已登录: {username}'))
            self.biliLoginCard.button.setText(self.tr('退出登录'))
            self.biliLoginCard.contentLabel.setStyleSheet(
                "QLabel#contentLabel { "
                "font: 11px 'Segoe UI', 'Microsoft YaHei', 'PingFang SC'; "
                "color: #10b981; "
                "padding: 0; "
                "}"
            )
        else:
            # 未登录状态
            self.biliLoginCard.setContent(self.tr('登录B站账号以获取更多功能'))
            self.biliLoginCard.button.setText(self.tr('登录'))
            # 恢复默认样式
            self.biliLoginCard.contentLabel.setStyleSheet("")
    
    def _isBiliLoggedIn(self):
        """检查是否已登录B站"""
        
        bili_login = BilibiliLogin()
        if bili_login.load_cookies():
            user_info = bili_login.get_user_info()
            return user_info and not user_info.get('isLogin', False) == False
        return False
    
    def _logoutBili(self):
        """退出B站登录"""

        login_file = str(LOGIN_FILE_PATH)
        
        try:
            if os.path.exists(login_file):
                os.remove(login_file)
            
            # 更新UI
            self._updateBiliLoginUI(False)

            InfoBar.success(
                title="退出成功",
                content="已成功退出B站账号",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self.window()
            )
        except Exception as e:
            # 直接显示退出失败提示
            InfoBar.error(
                title="退出失败",
                content=f"退出登录时发生错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )


class DownloadSettingsPage(QWidget):
    """ 下载设置页面 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("download")
        self.expandLayout = ExpandLayout(self)
        
        # 下载路径组
        self.pathGroup = SettingCardGroup(self.tr('下载路径'), self)
        
        self.downloadFolderCard = PushSettingCard(
            self.tr('选择文件夹'),
            FIF.DOWNLOAD,
            self.tr('下载目录'),
            str(config.get(config.downloadFolder)),
            self.pathGroup
        )
        
        self.cacheFolderCard = PushSettingCard(
            self.tr('选择文件夹'),
            FIF.FOLDER,
            self.tr('缓存目录'),
            str(config.get(config.cacheFolder)),
            self.pathGroup
        )
        
        self.__initLayout()
        self.__connectSignalToSlot()
    
    def __initLayout(self):
        self.pathGroup.addSettingCard(self.downloadFolderCard)
        self.pathGroup.addSettingCard(self.cacheFolderCard)
        
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(0, 0, 0, 0)
        self.expandLayout.addWidget(self.pathGroup)
    
    def __connectSignalToSlot(self):
        self.downloadFolderCard.clicked.connect(self.__onDownloadFolderCardClicked)
        self.cacheFolderCard.clicked.connect(self.__onCacheFolderCardClicked)
    
    def __onDownloadFolderCardClicked(self):
        """ 下载文件夹卡片点击槽函数 """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("选择文件夹"), "./")
        if not folder or config.get(config.downloadFolder) == folder:
            return
        
        config.set(config.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)
    
    def __onCacheFolderCardClicked(self):
        """ 缓存文件夹卡片点击槽函数 """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("选择文件夹"), "./")
        if not folder or config.get(config.cacheFolder) == folder:
            return
        
        config.set(config.cacheFolder, folder)
        self.cacheFolderCard.setContent(folder)


class OtherSettingsPage(QWidget):
    """ 其他设置页面 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("other")
        self.expandLayout = ExpandLayout(self)
        
        # 更新设置组
        self.updateGroup = SettingCardGroup(self.tr('软件更新'), self)
        
        self.updateOnStartUpCard = SwitchSettingCard(
            FIF.UPDATE,
            self.tr('启动时检查更新'),
            self.tr('应用程序启动时检查新版本'),
            configItem=config.checkUpdateAtStartUp,
            parent=self.updateGroup
        )
        
        self.__initLayout()
    
    def __initLayout(self):
        self.updateGroup.addSettingCard(self.updateOnStartUpCard)
        
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(0, 0, 0, 0)
        self.expandLayout.addWidget(self.updateGroup)


class AboutAuthorPage(QWidget):
    """ 关于作者页面 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("about")
        self.expandLayout = ExpandLayout(self)
        
        # 关于组
        self.aboutGroup = SettingCardGroup(self.tr('关于'), self)
        
        self.helpCard = HyperlinkCard(
            "https://github.com/",
            self.tr('打开帮助页面'),
            FIF.HELP,
            self.tr('帮助'),
            self.tr('获取使用帮助和常见问题解答'),
            self.aboutGroup
        )
        
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('提供反馈'),
            FIF.FEEDBACK,
            self.tr('提供反馈'),
            self.tr('通过提供反馈帮助我们改进VidFlow'),
            self.aboutGroup
        )
        
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('检查更新'),
            FIF.INFO,
            self.tr('关于'),
            '© ' + self.tr('版权所有') + ' 2024, VidFlow开发团队. ' +
            self.tr('版本') + ' 1.0.0',
            self.aboutGroup
        )
        
        self.__initLayout()
        self.__connectSignalToSlot()
    
    def __initLayout(self):
        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)
        
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(0, 0, 0, 0)
        self.expandLayout.addWidget(self.aboutGroup)
    
    def __connectSignalToSlot(self):
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/")))