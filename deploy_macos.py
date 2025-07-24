#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS部署脚本 - 使用Nuitka构建VidFlowDesktop
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.common.config import VERSION, APP_NAME, AUTHOR, COPYRIGHT


def get_platform_info():
    """获取平台信息"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == 'darwin':
        if machine in ['arm64', 'aarch64']:
            return 'macos', 'arm64'
        else:
            return 'macos', 'x86_64'
    else:
        print(f"❌ 此脚本仅支持macOS平台，当前平台: {system}")
        sys.exit(1)

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 检查Nuitka
    try:
        import nuitka
        print(f"✅ Nuitka版本: {nuitka.__version__}")
    except ImportError:
        print("❌ 未安装Nuitka，请运行: pip install nuitka")
        sys.exit(1)
    
    # 检查PyQt5
    try:
        import PyQt5
        print(f"✅ PyQt5已安装")
    except ImportError:
        print("❌ 未安装PyQt5，请运行: pip install PyQt5")
        sys.exit(1)

def create_app_icon():
    """创建应用图标"""
    icon_dir = Path("app/resource/images")
    icon_path = icon_dir / "logo.icns"
    
    if not icon_path.exists():
        print("⚠️ 应用图标不存在，创建占位符图标...")
        icon_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用系统默认图标作为占位符
        system_icon = "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns"
        if os.path.exists(system_icon):
            subprocess.run([
                "sips", "-s", "format", "icns", 
                system_icon, "--out", str(icon_path)
            ], check=True)
            print(f"✅ 创建占位符图标: {icon_path}")
        else:
            print("⚠️ 无法创建图标，将使用默认图标")
            return None
    
    return str(icon_path)

def build_macos_app(arch):
    """构建macOS应用"""
    print(f"🔨 开始构建macOS应用 ({arch})...")
    
    # 创建输出目录
    output_dir = Path("dist")
    output_dir.mkdir(exist_ok=True)
    
    # 获取图标路径
    icon_path = create_app_icon()
    
    # 构建Nuitka命令
    nuitka_args = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--plugin-enable=pyqt5",
        "--include-qt-plugins=sensible,sqldrivers",
        "--show-memory",
        "--show-progress",
        "--macos-create-app-bundle",
        "--assume-yes-for-downloads",
        "--macos-disable-console",
        f"--macos-app-version={VERSION}",
        f"--macos-app-name={APP_NAME}",
        f"--copyright={VERSION} {COPYRIGHT}",
        f"--output-dir={output_dir}",
    ]
    
    # 添加图标参数
    if icon_path:
        nuitka_args.append(f"--macos-app-icon={icon_path}")
    
    # 添加主程序文件
    nuitka_args.append("VidFlowDesktop.py")
    
    print(f"📝 执行命令: {' '.join(nuitka_args)}")
    
    # 执行构建
    try:
        result = subprocess.run(nuitka_args, check=True, capture_output=True, text=True)
        print("✅ Nuitka构建完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ Nuitka构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        sys.exit(1)
    
    # 设置可执行权限
    app_path = output_dir / f"{APP_NAME}.app"
    executable_path = app_path / "Contents/MacOS" / APP_NAME
    
    if executable_path.exists():
        os.chmod(executable_path, 0o755)
        print("✅ 设置可执行权限")
    
    # 清理构建文件
    build_dir = output_dir / f"{APP_NAME}.build"
    if build_dir.exists():
        import shutil
        shutil.rmtree(build_dir)
        print("🧹 清理构建文件")
    
    return app_path

def download_ffmpeg(app_path, arch):
    """下载并安装FFmpeg"""
    print(f"📥 下载FFmpeg ({arch})...")
    
    # 创建FFmpeg目录
    ffmpeg_dir = app_path / "Contents/MacOS/ffmpeg"
    ffmpeg_dir.mkdir(parents=True, exist_ok=True)
    
    # FFmpeg下载URL
    ffmpeg_url = "https://evermeet.cx/ffmpeg/getrelease/zip"
    
    # 下载FFmpeg
    import urllib.request
    import zipfile
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "ffmpeg.zip"
        
        print(f"📥 从 {ffmpeg_url} 下载FFmpeg...")
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        
        # 解压FFmpeg
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_path)
        
        # 复制FFmpeg到应用包
        ffmpeg_src = temp_path / "ffmpeg"
        ffmpeg_dst = ffmpeg_dir / "ffmpeg"
        
        if ffmpeg_src.exists():
            import shutil
            shutil.copy2(ffmpeg_src, ffmpeg_dst)
            os.chmod(ffmpeg_dst, 0o755)
            print(f"✅ FFmpeg安装到: {ffmpeg_dst}")
        else:
            print("❌ FFmpeg下载失败")
            sys.exit(1)

def fix_ffmpeg_path(app_path):
    """修复FFmpeg路径"""
    print("🔧 修复FFmpeg路径...")
    
    # 查找threadManager.py文件
    thread_manager_paths = [
        app_path / "Contents/MacOS/app/common/threadManager.py",
        app_path / "Contents/Resources/app/common/threadManager.py",
    ]
    
    thread_manager_path = None
    for path in thread_manager_paths:
        if path.exists():
            thread_manager_path = path
            break
    
    if not thread_manager_path:
        print("⚠️ 未找到threadManager.py文件")
        return
    
    # 读取文件内容
    with open(thread_manager_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换FFmpeg路径
    original_content = content
    content = content.replace("'ffmpeg', 'ffmpeg.exe'", "'ffmpeg', 'ffmpeg'")
    content = content.replace('"ffmpeg", "ffmpeg.exe"', '"ffmpeg", "ffmpeg"')
    
    # 如果有修改，写回文件
    if content != original_content:
        with open(thread_manager_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ FFmpeg路径已修复: {thread_manager_path}")
    else:
        print("ℹ️ FFmpeg路径无需修复")

def create_dmg(app_path, arch):
    """创建DMG安装包"""
    print("📦 创建DMG安装包...")
    
    dmg_name = f"{APP_NAME}-v{VERSION}-macOS-{arch}.dmg"
    
    # 创建临时目录
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        dmg_temp = temp_path / "dmg_temp"
        dmg_temp.mkdir()
        
        # 复制应用到临时目录
        shutil.copytree(app_path, dmg_temp / app_path.name)
        
        # 创建Applications链接
        applications_link = dmg_temp / "Applications"
        applications_link.symlink_to("/Applications")
        
        # 尝试使用create-dmg
        try:
            icon_path = create_app_icon()
            create_dmg_args = [
                "create-dmg",
                "--volname", APP_NAME,
                "--window-pos", "200", "120",
                "--window-size", "800", "450",
                "--icon-size", "100",
                "--icon", f"{APP_NAME}.app", "200", "190",
                "--hide-extension", f"{APP_NAME}.app",
                "--app-drop-link", "600", "185",
                "--hdiutil-quiet",
                dmg_name,
                str(dmg_temp)
            ]
            
            if icon_path:
                create_dmg_args.extend(["--volicon", icon_path])
            
            subprocess.run(create_dmg_args, check=True)
            print(f"✅ 使用create-dmg创建DMG: {dmg_name}")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ create-dmg失败，使用hdiutil...")
            
            # 使用hdiutil作为备选
            hdiutil_args = [
                "hdiutil", "create",
                "-srcfolder", str(dmg_temp),
                "-volname", APP_NAME,
                "-fs", "HFS+",
                "-fsargs", "-c c=64,a=16,e=16",
                "-format", "UDZO",
                "-size", "400m",
                dmg_name
            ]
            
            subprocess.run(hdiutil_args, check=True)
            print(f"✅ 使用hdiutil创建DMG: {dmg_name}")
    
    # 验证DMG文件
    dmg_path = Path(dmg_name)
    if dmg_path.exists():
        size_mb = dmg_path.stat().st_size / (1024 * 1024)
        print(f"✅ DMG创建成功: {dmg_name} ({size_mb:.1f} MB)")
        return dmg_path
    else:
        print(f"❌ DMG创建失败: {dmg_name}")
        sys.exit(1)

def main():
    """主函数"""
    print(f"🚀 开始构建 {APP_NAME} v{VERSION} for macOS")
    
    # 获取平台信息
    platform_name, arch = get_platform_info()
    print(f"📱 目标平台: {platform_name} ({arch})")
    
    # 检查依赖
    check_dependencies()
    
    # 构建应用
    app_path = build_macos_app(arch)
    
    # 下载FFmpeg
    download_ffmpeg(app_path, arch)
    
    # 修复FFmpeg路径
    fix_ffmpeg_path(app_path)
    
    # 创建DMG
    dmg_path = create_dmg(app_path, arch)
    
    print(f"🎉 构建完成!")
    print(f"📦 应用包: {app_path}")
    print(f"💿 安装包: {dmg_path}")
    print(f"")
    print(f"📋 安装说明:")
    print(f"1. 双击 {dmg_path.name} 打开安装包")
    print(f"2. 将 {APP_NAME}.app 拖拽到 Applications 文件夹")
    print(f"3. 首次运行可能需要在系统偏好设置中允许")

if __name__ == "__main__":
    main()