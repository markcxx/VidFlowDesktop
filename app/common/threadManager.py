import json
import re
import os
import requests
import subprocess
import tempfile
import shutil
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from urllib.parse import urlparse

from .config import API_URL, config
from .bilibili_login import BilibiliLogin


class ParsingVideoThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, share_link):
        super(ParsingVideoThread, self).__init__()
        self.shareUrl = ""
        self.shareLink = share_link

    def run(self):
        """线程运行方法"""
        try:
            # 提取URL并检测平台
            url = self.extract_url_from_text(self.shareLink)
            platform = self.detect_platform(url)
            
            if not platform:
                self.error.emit('不支持的视频平台')
                return
            
            # 平台解析器映射
            parsers = {
                'douyin': self.parse_douyin_video,
                'bilibili': self.parse_bilibili_video
            }
            
            # 执行解析
            parser = parsers.get(platform)
            data = parser(url) if parser else None
            
            if data:
                self.finished.emit(data)
            else:
                platform_names = {'douyin': '抖音', 'bilibili': 'B站'}
                self.error.emit(f'{platform_names.get(platform, platform)}视频解析失败')
                
        except Exception as e:
            self.error.emit(f'解析过程中发生错误: {str(e)}')

    @staticmethod
    def extract_url_from_text(text: str) -> str:
        """从分享文本中提取URL"""
        # URL匹配模式
        patterns = [
            r'(https?://[^\s]+)',  # 完整URL
            r'(v\.douyin\.com/[A-Za-z0-9]+)'  # 抖音短链接
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                url = matches[0]
                return url if url.startswith('http') else f"https://{url}"
        
        return text.strip()

    @staticmethod
    def detect_platform(url: str) -> Optional[str]:
        """检测视频平台类型"""
        platform_patterns = {
            'douyin': ['douyin.com', 'v.douyin.com'],
            'bilibili': ['bilibili.com', 'b23.tv']
        }
        
        for platform, patterns in platform_patterns.items():
            if any(pattern in url for pattern in patterns):
                return platform
        
        return None



    def _make_api_request(self, endpoint: str, url: str) -> Optional[Dict[str, Any]]:
        """通用API请求方法"""
        try:
            response = requests.post(
                f"{API_URL}{endpoint}",
                headers={'Content-Type': 'application/json'},
                json={'url': url}
            )
            
            if not response.ok:
                return None
                
            api_response = response.json()
            return api_response if api_response.get('code') == 200 else None
            
        except (requests.RequestException, json.JSONDecodeError):
            return None
    
    def parse_douyin_video(self, url: str) -> Optional[Dict[str, Any]]:
        """解析抖音视频"""
        api_response = self._make_api_request('/api/parse_video', url)
        if not api_response:
            return None
            
        data = api_response['data']
        # 提取标签
        caption = data.get('caption', '')
        tags = [tag[1:] for tag in re.findall(r'#[^\s#]+', caption)]
        
        data.update({
            'tags': tags,
            'platform': '抖音'
        })
        return data

    def parse_bilibili_video(self, url: str) -> Optional[Dict[str, Any]]:
        """解析B站视频"""
        # 检查是否已登录B站
        bili_login = BilibiliLogin()
        is_logged_in = False
        
        # 尝试加载已保存的cookies
        if bili_login.load_cookies():
            user_info = bili_login.get_user_info()
            if user_info and not user_info.get('isLogin', False) == False:
                is_logged_in = True
        
        if is_logged_in:
            # 已登录，使用带cookies的直接请求
            return self._parse_bilibili_with_login(url, bili_login)
        else:
            # 未登录，使用API请求
            api_response = self._make_api_request('/api/parse_bilibili', url)
            if not api_response:
                return None
                
            data = api_response['data']
            data['platform'] = 'B站'
            return data
    
    def _parse_bilibili_with_login(self, url: str, bili_login: BilibiliLogin) -> Optional[Dict[str, Any]]:
        """使用登录状态解析B站视频"""
        try:
            # 提取BV号或AV号
            bv_match = re.search(r'[Bb][Vv]([A-Za-z0-9]+)', url)
            av_match = re.search(r'av(\d+)', url)
            
            if bv_match:
                bvid = 'BV' + bv_match.group(1)
                params = {'bvid': bvid}
            elif av_match:
                aid = av_match.group(1)
                params = {'aid': aid}
            else:
                return None
            
            # 获取视频基本信息
            response = requests.get(
                'https://api.bilibili.com/x/web-interface/view',
                headers=bili_login.headers,
                params=params
            )
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            if data.get('code') != 0:
                return None
                
            video_info = data['data']
            
            # 获取播放信息（包含下载链接）
            play_params = {
                'bvid': video_info.get('bvid'),
                'cid': video_info['pages'][0]['cid'],
                'qn': 80,  # 请求1080P质量
                'fnval': 4048,  # 请求DASH格式
                'fourk': 1
            }
            
            play_response = requests.get(
                'https://api.bilibili.com/x/player/playurl',
                headers=bili_login.headers,
                params=play_params
            )
            
            if play_response.status_code == 200:
                play_data = play_response.json()
                if play_data.get('code') == 0:
                    video_info['play_info'] = play_data['data']
            
            # 格式化返回数据
            video_info['platform'] = 'B站'
            return video_info
            
        except Exception as e:
            print(f"带登录解析B站视频失败: {e}")
            return None


class BilibiliDownloadThread(QThread):
    """B站视频下载线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, quality_data, video_info, parent=None):
        super().__init__(parent)
        self.quality_data = quality_data
        self.video_info = video_info
        self.is_stopped = False
        
    def run(self):
        """执行下载"""
        try:
            download_folder = str(config.downloadFolder.value)
            
            # 获取视频标题作为文件名
            title = self.video_info.get('title', 'bilibili_video')
            # 清理文件名
            title = self._sanitize_filename(title)
            
            # 检查是否为DASH格式（需要合并）
            if self.quality_data.get('type') == 'video' and 'dash' in self.video_info.get('play_info', {}):
                # DASH格式，需要下载视频和音频并合并
                self._download_dash_video_sync(download_folder, title)
            elif self.quality_data.get('type') in ['audio', 'audio_only']:
                # 仅下载音频
                self._download_audio_only_sync(download_folder, title)
            else:
                # 传统格式，直接下载
                self._download_traditional_video_sync(download_folder, title)
                
        except Exception as e:
            if not self.is_stopped:
                self.error.emit(f"下载失败: {str(e)}")
    
    def _download_dash_video_sync(self, download_folder, title):
        """下载DASH格式视频（需要合并音视频）"""
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 获取音频流（选择最高质量）
            play_info = self.video_info.get('play_info', {})
            audio_streams = play_info.get('dash', {}).get('audio', [])
            if not audio_streams:
                raise Exception("未找到音频流")
            
            best_audio = max(audio_streams, key=lambda x: x.get('bandwidth', 0))
            
            # 下载视频流
            video_url = self.quality_data.get('base_url', '')
            if not video_url:
                raise Exception("视频下载链接无效")
            
            video_temp_path = os.path.join(temp_dir, 'video.m4v')
            self._download_file_sync(video_url, video_temp_path, 'video')
            
            if self.is_stopped:
                return
            
            # 下载音频流
            audio_url = best_audio.get('base_url', '')
            if not audio_url:
                raise Exception("音频下载链接无效")
            
            audio_temp_path = os.path.join(temp_dir, 'audio.m4a')
            self._download_file_sync(audio_url, audio_temp_path, 'audio')
            
            if self.is_stopped:
                return

            # 使用FFmpeg合并
            output_path = os.path.join(download_folder, f"{title}.mp4")
            output_path = self._get_unique_filename(output_path)
            
            self._merge_video_audio_sync(video_temp_path, audio_temp_path, output_path)
            
            if not self.is_stopped:
                self.finished.emit(output_path)
                
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def _download_audio_only_sync(self, download_folder, title):
        """仅下载音频"""
        
        # 获取音频流（选择最高质量）
        play_info = self.video_info.get('play_info', {})
        audio_streams = play_info.get('dash', {}).get('audio', [])
        if not audio_streams:
            raise Exception("未找到音频流")
        
        best_audio = max(audio_streams, key=lambda x: x.get('bandwidth', 0))
        audio_url = best_audio.get('base_url', '')
        if not audio_url:
            raise Exception("音频下载链接无效")
        
        output_path = os.path.join(download_folder, f"{title}.m4a")
        output_path = self._get_unique_filename(output_path)
        
        self._download_file_sync(audio_url, output_path, 'audio')
        
        if not self.is_stopped:
            self.finished.emit(output_path)
    
    def _download_traditional_video_sync(self, download_folder, title):
        """下载传统格式视频"""
        import os
        
        video_url = self.quality_data.get('base_url', '')
        if not video_url:
            raise Exception("视频下载链接无效")
        
        output_path = os.path.join(download_folder, f"{title}.mp4")
        output_path = self._get_unique_filename(output_path)
        
        self._download_file_sync(video_url, output_path, 'video')
        
        if not self.is_stopped:
            self.finished.emit(output_path)
    
    def _download_file_sync(self, url, output_path, file_type):
        """下载文件"""

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/'
        }

        try:
            bili_login = BilibiliLogin()
            if bili_login.load_cookies():
                user_info = bili_login.get_user_info()
                if user_info and not user_info.get('isLogin', False) == False:
                    # 已登录，添加Cookie到请求头
                    cookies = bili_login.cookies
                    cookie_str = '; '.join([f'{k}={v}' for k, v in cookies.items()])
                    headers['Cookie'] = cookie_str
        except Exception as e:
            # 如果获取Cookie失败，继续使用基本请求头
            print(f"获取Cookie失败: {e}")
        
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code != 200:
            raise Exception(f"下载失败，状态码: {response.status_code}")
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if self.is_stopped:
                    return
                
                f.write(chunk)
                downloaded += len(chunk)
                
                if total_size > 0:
                    progress = int((downloaded / total_size) * 100)
                    self.progress.emit(progress)
    
    def _merge_video_audio_sync(self, video_path, audio_path, output_path):
        """使用FFmpeg合并视频和音频"""

        ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ffmpeg', 'ffmpeg.exe')
        
        if not os.path.exists(ffmpeg_path):
            raise Exception("FFmpeg未找到")
        
        # FFmpeg命令
        cmd = [
            ffmpeg_path,
            '-i', video_path,
            '-i', audio_path,
            '-c', 'copy',
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        # 执行FFmpeg
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"视频合并失败: {stderr.decode('utf-8', errors='ignore')}")
    
    def _sanitize_filename(self, filename):
        """清理文件名"""
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename
    
    def _get_unique_filename(self, filepath):
        """获取唯一文件名（避免重复）"""
        if not os.path.exists(filepath):
            return filepath
        
        base, ext = os.path.splitext(filepath)
        counter = 1
        
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    def stop(self):
        """停止下载"""
        self.is_stopped = True
        if self.isRunning():
            self.wait(3000)


class ImageLoaderThread(QThread):
    """网络图片加载线程类"""
    
    # 信号定义
    imageLoaded = pyqtSignal(QPixmap, str)  # 图片加载完成信号，传递QPixmap和图片类型
    loadFailed = pyqtSignal(str)            # 加载失败信号，传递图片类型
    
    def __init__(self, url, image_type, parent=None):
        super().__init__(parent)
        self.url = url
        self.image_type = image_type  # 'cover' 或 'avatar'
    
    def run(self):
        try:
            if not self.url:
                self.loadFailed.emit(self.image_type)
                return

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(
                self.url, 
                headers=headers,
                timeout=10,
                stream=True
            )
            
            if response.status_code == 200:
                # 创建QPixmap对象并加载图片数据
                pixmap = QPixmap()
                success = pixmap.loadFromData(response.content)
                
                if success and not pixmap.isNull():
                    self.imageLoaded.emit(pixmap, self.image_type)
                else:
                    self.loadFailed.emit(self.image_type)
            else:
                self.loadFailed.emit(self.image_type)
                
        except requests.exceptions.Timeout:
            self.loadFailed.emit(self.image_type)
        except requests.exceptions.RequestException:
            self.loadFailed.emit(self.image_type)
        except Exception:
            self.loadFailed.emit(self.image_type)
    
    def stop(self):
        """停止线程"""
        self.terminate()
        self.wait()


class VideoDownloadThread(QThread):
    """视频下载线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, download_url, save_directory=None, filename=None, resolution=None):
        super(VideoDownloadThread, self).__init__()
        self.download_url = download_url
        self.save_directory = save_directory or str(config.downloadFolder.value)
        self.filename = filename
        self.resolution = resolution
        self._is_cancelled = False
    
    def run(self):
        """执行下载"""
        try:
            os.makedirs(self.save_directory, exist_ok=True)

            if not self.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                resolution_str = self.resolution or "unknown"
                self.filename = f"{timestamp}_{resolution_str}.mp4"

            if not os.path.splitext(self.filename)[1]:
                self.filename += '.mp4'
            
            file_path = os.path.join(self.save_directory, self.filename)

            counter = 1
            original_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_path)
                file_path = f"{name}({counter}){ext}"
                counter += 1
            
            # 开始下载
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.download_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._is_cancelled:
                        file.close()
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return
                    
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)

                        if total_size > 0:
                            progress_percent = int((downloaded_size / total_size) * 100)
                            self.progress.emit(progress_percent)
            
            # 下载完成
            self.progress.emit(100)
            self.finished.emit(file_path)
            
        except requests.exceptions.RequestException as e:
            self.error.emit(f"网络错误: {str(e)}")
        except OSError as e:
            self.error.emit(f"文件操作错误: {str(e)}")
        except Exception as e:
            self.error.emit(f"下载失败: {str(e)}")
    
    def cancel(self):
        """取消下载"""
        self._is_cancelled = True
    
    def stop(self):
        """停止线程"""
        self.cancel()
        if self.isRunning():
            self.wait(3000)


class AudioDownloadThread(QThread):
    """音频下载线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, download_url, save_directory=None):
        super(AudioDownloadThread, self).__init__()
        self.download_url = download_url
        self.save_directory = save_directory or str(config.downloadFolder.value)
        self._is_cancelled = False
    
    def run(self):
        try:
            os.makedirs(self.save_directory, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}.mp3"
            file_path = os.path.join(self.save_directory, filename)

            counter = 1
            original_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_path)
                file_path = f"{name}({counter}){ext}"
                counter += 1
            
            # 开始下载
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.download_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._is_cancelled:
                        file.close()
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return
                    
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)

                        if total_size > 0:
                            progress_percent = int((downloaded_size / total_size) * 100)
                            self.progress.emit(progress_percent)
            
            # 下载完成
            self.progress.emit(100)
            self.finished.emit(file_path)
            
        except requests.exceptions.RequestException as e:
            self.error.emit(f"网络错误: {str(e)}")
        except OSError as e:
            self.error.emit(f"文件操作错误: {str(e)}")
        except Exception as e:
            self.error.emit(f"下载失败: {str(e)}")
    
    def cancel(self):
        """取消下载"""
        self._is_cancelled = True
    
    def stop(self):
        """停止线程"""
        self.cancel()
        if self.isRunning():
            self.wait(3000)  # 等待最多3秒


