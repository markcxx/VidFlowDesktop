# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """ Signal bus """

    appMessageSig = pyqtSignal(str)
    appErrorSig = pyqtSignal(str)

    checkUpdateSig = pyqtSignal()
    micaEnableChanged = pyqtSignal(bool)

    downloadTerminated = pyqtSignal(int, bool)

    switchToTaskInterfaceSig = pyqtSignal()

    showUnsureSignal = pyqtSignal()
    hideUnsureSignal = pyqtSignal()

    # 视频质量选择信号（保留用于下载逻辑）
    videoQualitySelectedSig = pyqtSignal(dict)  # 用户选择了某个质量选项
    bilibiliQualitySelectedSig = pyqtSignal(dict)  # 用户选择了B站视频质量选项
    
    # 视频下载相关信号（保留用于下载逻辑）
    startVideoDownloadSig = pyqtSignal(dict)      # 开始下载视频，传入质量数据
    
    # 音频下载相关信号（保留用于下载逻辑）
    startAudioDownloadSig = pyqtSignal(dict)      # 开始下载音频，传入视频信息
    
    # B站下载相关信号
    startBilibiliDownloadSig = pyqtSignal(dict)   # 开始B站视频下载，传入质量数据

signalBus = SignalBus()