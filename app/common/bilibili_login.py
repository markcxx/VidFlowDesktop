#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站登录核心模块
基于测试文件中的登录逻辑实现
"""

import json
import time
import hashlib
import urllib.parse
import os
from typing import Dict, Optional
from PyQt5.QtCore import QThread, pyqtSignal
import requests
import qrcode
from io import BytesIO
from .config import LOGIN_FILE_PATH


class BilibiliLogin:
    """B站登录核心类"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com'
        }
        self.cookies = {}
        self.qrcode_key = None

    def init_client(self) -> bool:
        """初始化客户端，获取基础Cookie"""
        try:
            # 获取buvid3和buvid4
            response = requests.get('https://www.bilibili.com/', headers=self.headers)
            for cookie in response.cookies:
                self.cookies[cookie.name] = cookie.value

            # 获取bili_ticket
            finger_data = {
                'platform': 'web',
                'webid': self.cookies.get('buvid3', ''),
            }

            response = requests.post(
                'https://api.bilibili.com/x/frontend/finger/spi',
                headers=self.headers,
                json=finger_data
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    bili_ticket = data.get('data', {}).get('b_3', '')
                    if bili_ticket:
                        self.cookies['bili_ticket'] = bili_ticket

            self._update_headers()
            return True

        except Exception as e:
            print(f"初始化客户端失败: {e}")
            return False

    def _update_headers(self):
        """更新请求头中的Cookie"""
        cookie_str = '; '.join([f'{k}={v}' for k, v in self.cookies.items()])
        self.headers['Cookie'] = cookie_str

    def get_qrcode(self) -> Optional[bytes]:
        """获取登录二维码"""
        try:
            response = requests.get(
                'https://passport.bilibili.com/x/passport-login/web/qrcode/generate',
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    qr_data = data.get('data', {})
                    self.qrcode_key = qr_data.get('qrcode_key')
                    qr_url = qr_data.get('url')

                    if qr_url and self.qrcode_key:
                        # 生成二维码图片
                        qr = qrcode.QRCode(version=1, box_size=10, border=5)
                        qr.add_data(qr_url)
                        qr.make(fit=True)

                        img = qr.make_image(fill_color="black", back_color="white")

                        # 转换为字节流
                        img_buffer = BytesIO()
                        img.save(img_buffer, format='PNG')
                        return img_buffer.getvalue()

            return None

        except Exception as e:
            print(f"获取二维码失败: {e}")
            return None

    def check_login_status(self) -> Dict[str, any]:
        """检查登录状态"""
        if not self.qrcode_key:
            return {'code': -1, 'message': '二维码key不存在'}

        try:
            params = {'qrcode_key': self.qrcode_key}
            response = requests.get(
                'https://passport.bilibili.com/x/passport-login/web/qrcode/poll',
                headers=self.headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                code = data.get('data', {}).get('code', -1)

                if code == 0:  # 登录成功
                    # 提取Cookie
                    for cookie in response.cookies:
                        self.cookies[cookie.name] = cookie.value

                    # 获取refresh_token等关键信息
                    refresh_token = data.get('data', {}).get('refresh_token', '')
                    if refresh_token:
                        self.cookies['refresh_token'] = refresh_token

                    self._update_headers()
                    return {'code': 0, 'message': '登录成功'}

                elif code == 86101:  # 未扫码
                    return {'code': 86101, 'message': '等待扫码'}

                elif code == 86090:  # 已扫码未确认
                    return {'code': 86090, 'message': '已扫码，等待确认'}

                elif code == 86038:  # 二维码过期
                    return {'code': 86038, 'message': '二维码已过期'}

                else:
                    return {'code': code, 'message': data.get('message', '未知错误')}

            return {'code': -1, 'message': '网络请求失败'}

        except Exception as e:
            return {'code': -1, 'message': f'检查登录状态失败: {e}'}

    def save_cookies(self, filepath: str = None) -> bool:
        """保存Cookie到文件"""
        if filepath is None:
            # 使用配置的登录文件路径
            filepath = str(LOGIN_FILE_PATH)
        
        try:
            login_data = {
                'cookies': self.cookies,
                'login_time': time.time(),
                'platform': 'bilibili'
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(login_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存Cookie失败: {e}")
            return False

    def load_cookies(self, filepath: str = None) -> bool:
        """从文件加载Cookie"""
        if filepath is None:
            # 使用配置的登录文件路径
            filepath = str(LOGIN_FILE_PATH)
        
        # 检查文件是否存在，避免显示不必要的警告
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                login_data = json.load(f)
            
            if 'cookies' in login_data:
                self.cookies = login_data['cookies']
            else:
                self.cookies = login_data
            
            self._update_headers()
            return True
        except Exception as e:
            print(f"加载Cookie失败: {e}")
            return False

    def get_user_info(self) -> Optional[Dict]:
        """获取用户信息，验证登录状态"""
        try:
            response = requests.get(
                'https://api.bilibili.com/x/web-interface/nav',
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    return data.get('data')

            return None

        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None


class LoginThread(QThread):
    """登录状态检查线程"""

    status_changed = pyqtSignal(dict)

    def __init__(self, bili_login):
        super().__init__()
        self.bili_login = bili_login
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            status = self.bili_login.check_login_status()
            self.status_changed.emit(status)

            if status['code'] == 0:  # 登录成功
                break
            elif status['code'] == 86038:  # 二维码过期
                break

            time.sleep(2)  # 每2秒检查一次

    def stop(self):
        self.running = False
        self.quit()
        self.wait()