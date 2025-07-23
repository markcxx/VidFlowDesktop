# coding:utf-8
# @Time    : 2025/1/27
# @Author  : Assistant
# @FileName: bili_login_dialog.py

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QStackedWidget, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap
from qfluentwidgets import (
    Dialog, PushButton, LineEdit, CheckBox, SegmentedWidget,
    TitleLabel, BodyLabel, InfoBar, InfoBarPosition, FluentIcon, TransparentToolButton
)

from ..common.style_sheet import setStyleSheet
from ..common.bilibili_login import BilibiliLogin, LoginThread


class QRCodeWidget(QWidget):
    """二维码显示组件"""
    login_success = pyqtSignal()  # 登录成功信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = "waiting"  # waiting, scanned, expired
        
        # 初始化B站登录
        self.bili_login = BilibiliLogin()
        self.login_thread = None
        
        # 初始化UI
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # 二维码显示区域
        self.qr_label = QLabel("二维码加载中...", self)
        self.qr_label.setFixedSize(200, 200)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setObjectName("qrLabel")
        self.qr_label.setProperty("status", "waiting")

        # 状态提示
        self.status_label = BodyLabel("请使用哔哩哔哩客户端扫码登录", self)
        self.status_label.setAlignment(Qt.AlignCenter)

        # 刷新按钮（初始隐藏）
        self.refresh_btn = PushButton("点击刷新", self)
        self.refresh_btn.setFixedWidth(100)
        self.refresh_btn.hide()
        self.refresh_btn.clicked.connect(self.refresh_qr)

        layout.addWidget(self.qr_label)
        layout.addSpacing(10)
        layout.addWidget(self.status_label)
        layout.addWidget(self.refresh_btn, alignment=Qt.AlignCenter)
        self.set_qss()

        # 自动获取二维码
        QTimer.singleShot(500, self.get_qrcode)

    def set_qss(self):
        setStyleSheet(self, 'bili_login_dialog')
#         self.qr_label.setStyleSheet("""
#         #qrLabel[status="waiting"] {
#     border: 2px dashed #E0E0E0;
#     border-radius: 10px;
#     background-color: #F8F9FA;
#     color: #666;
#     font-size: 14px;
# }
#         """)

    def get_qrcode(self):
        """获取二维码"""
        self.status_label.setText("正在获取二维码...")
        
        # 初始化客户端
        if not self.bili_login.init_client():
            self.status_label.setText("初始化失败，请重试")
            self.refresh_btn.show()
            return
        
        # 获取二维码
        qr_data = self.bili_login.get_qrcode()
        if qr_data:
            pixmap = QPixmap()
            pixmap.loadFromData(qr_data)
            scaled_pixmap = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.qr_label.setPixmap(scaled_pixmap)
            self.qr_label.setText("")
            
            self.set_status("waiting")
            self.start_login_check()
        else:
            self.status_label.setText("获取二维码失败，请重试")
            self.refresh_btn.show()
    
    def start_login_check(self):
        """开始检查登录状态"""
        if self.login_thread:
            self.login_thread.stop()
        
        self.login_thread = LoginThread(self.bili_login)
        self.login_thread.status_changed.connect(self.on_login_status_changed)
        self.login_thread.start()
    
    def on_login_status_changed(self, status):
        """登录状态变化处理"""
        code = status['code']
        message = status['message']
        
        if code == 0:  # 登录成功
            self.set_status("success")
            # 保存Cookie
            if self.bili_login.save_cookies():
                self.login_success.emit()
        elif code == 86101:
            self.set_status("waiting")
        elif code == 86090:
            self.set_status("scanned")
        elif code == 86038:
            self.set_status("expired")
        else:
            self.status_label.setText(f"错误: {message}")
            self.refresh_btn.show()

    def set_status(self, status):
        """设置二维码状态"""
        self.status = status
        if status == "waiting":
            self.qr_label.setProperty("status", "waiting")
            self.status_label.setText("请使用哔哩哔哩客户端扫码登录")
            self.refresh_btn.hide()
        elif status == "scanned":
            self.qr_label.setProperty("status", "scanned")
            self.status_label.setText("扫码成功，请在手机上确认登录")
            self.refresh_btn.hide()
        elif status == "expired":
            self.qr_label.setText("二维码已过期")
            self.qr_label.setProperty("status", "expired")
            self.status_label.setText("二维码已失效")
            self.refresh_btn.show()
        elif status == "success":
            self.qr_label.setText("登录成功")
            self.qr_label.setProperty("status", "success")
            self.status_label.setText("登录成功！")
            self.refresh_btn.hide()
        
        # 更新样式
        self.qr_label.style().unpolish(self.qr_label)
        self.qr_label.style().polish(self.qr_label)

    def refresh_qr(self):
        """刷新二维码"""
        if self.login_thread:
            self.login_thread.stop()
        self.get_qrcode()

    def set_qr_pixmap(self, pixmap):
        """设置二维码图片"""
        self.qr_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.qr_label.setText("")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.login_thread:
            self.login_thread.stop()
        event.accept()


class PasswordWidget(QWidget):
    """密码登录组件"""
    login_success = pyqtSignal()  # 登录成功信号

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化UI
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 用户名输入
        self.username_label = BodyLabel("手机号/邮箱", self)
        self.username_edit = LineEdit(self)
        self.username_edit.setPlaceholderText("请输入手机号或邮箱")
        self.username_edit.setFixedHeight(40)

        # 密码输入
        self.password_label = BodyLabel("密码", self)
        self.password_edit = LineEdit(self)
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(LineEdit.Password)
        self.password_edit.setFixedHeight(40)

        # 回车键登录
        self.password_edit.returnPressed.connect(self.login)

        # 记住我选项
        self.remember_cb = CheckBox("记住我", self)

        # 登录按钮
        self.login_btn = PushButton("登录", self)
        self.login_btn.setFixedHeight(40)
        self.login_btn.clicked.connect(self.login)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.remember_cb)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn)

    def login(self):
        """登录处理"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            InfoBar.warning(
                title="提示",
                content="请输入用户名和密码",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 模拟登录验证
        self.login_btn.setText("登录中...")
        self.login_btn.setEnabled(False)

        # 模拟网络延迟
        QTimer.singleShot(1000, self.handle_login_result)

    def handle_login_result(self):
        """处理登录结果"""
        self.login_btn.setText("登录")
        self.login_btn.setEnabled(True)

        # 这里可以添加实际的登录验证逻辑
        # 现在模拟登录成功
        self.login_success.emit()


class BiliLoginDialog(Dialog):
    """哔哩哔哩登录对话框"""

    def __init__(self, parent=None):
        super().__init__("", "", parent)
        
        # 设置对话框大小和标题
        self.setFixedSize(450, 400)
        self.setWindowTitle("登录哔哩哔哩")
        self.setObjectName("biliLoginDialog")

        # 清空默认内容
        self.titleLabel.hide()
        self.contentLabel.hide()
        self.textLayout.removeWidget(self.contentLabel)
        self.textLayout.removeWidget(self.titleLabel)
        self.titleLabel.deleteLater()
        self.contentLabel.deleteLater()

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(30, 0, 10, 0)

        # 头部区域
        header_layout = QHBoxLayout()

        # 标题区域
        title_layout = QVBoxLayout()
        self.title = TitleLabel("登录哔哩哔哩", self)
        self.subtitle = BodyLabel("你感兴趣的视频都在B站", self)
        self.subtitle.setObjectName("subtitle")

        title_layout.addWidget(self.title)
        title_layout.addWidget(self.subtitle)

        # 关闭按钮
        self.close_btn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.clicked.connect(self.reject)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        # 关闭按钮不添加到布局中，而是通过绝对定位

        # 选项卡切换
        self.segment = SegmentedWidget(self)
        self.segment.addItem("qr", "扫码登录", lambda: self.switch_tab(0))
        self.segment.addItem("password", "密码登录", lambda: self.switch_tab(1))
        self.segment.setCurrentItem("qr")

        # 内容区域
        self.content_stack = QStackedWidget(self)

        # 二维码登录页面
        self.qr_widget = QRCodeWidget(self)
        self.qr_widget.setObjectName("qrWidget")
        self.qr_widget.login_success.connect(self.on_login_success)
        self.content_stack.addWidget(self.qr_widget)

        # 密码登录页面
        self.password_widget = PasswordWidget(self)
        self.password_widget.login_success.connect(self.on_login_success)
        self.content_stack.addWidget(self.password_widget)

        # 添加到布局
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.segment)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.content_stack)
        main_layout.addStretch()

        # 设置内容布局
        content_widget = QWidget(self)
        content_widget.setLayout(main_layout)

        # 替换对话框内容
        self.textLayout.addWidget(content_widget)

        # 隐藏默认按钮
        self.yesButton.hide()
        self.cancelButton.hide()
        self.buttonLayout.setContentsMargins(20, 0, 20, 0)
        self.buttonGroup.setFixedHeight(0)
        self.textLayout.setContentsMargins(24, 0, 24, 0)
        
        # 设置样式
        self.setQss()
        
        # 更新关闭按钮位置
        self.updateCloseButtonPosition()
        
        # 重写resizeEvent以保持按钮位置
        self._originalResizeEvent = self.resizeEvent
        self.resizeEvent = self._customResizeEvent

    def updateCloseButtonPosition(self):
        """更新关闭按钮位置"""
        if hasattr(self, 'close_btn'):
            self.close_btn.move(self.width() - 40, 8)
            self.close_btn.raise_()
            
    def _customResizeEvent(self, event):
        """自定义resize事件，保持关闭按钮在右上角"""
        if hasattr(self, '_originalResizeEvent'):
            self._originalResizeEvent(event)
        self.updateCloseButtonPosition()
    
    def setQss(self):
        """设置样式"""
        setStyleSheet(self.subtitle, "bili_login_dialog")
    def switch_tab(self, index):
        """切换选项卡"""
        self.content_stack.setCurrentIndex(index)

    def on_login_success(self):
        """登录成功处理"""
        # 显示成功消息
        InfoBar.success(
            title="登录成功",
            content="欢迎回来！",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self
        )

        # 延迟关闭对话框
        QTimer.singleShot(1500, self.accept)

    def get_qr_widget(self):
        """获取二维码组件，用于外部设置二维码图片"""
        return self.qr_widget

    def closeEvent(self, event):
        """重写关闭事件"""
        # 停止登录线程
        if hasattr(self.qr_widget, 'login_thread') and self.qr_widget.login_thread:
            self.qr_widget.login_thread.stop()
        self.reject()
        event.accept()