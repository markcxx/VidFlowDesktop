#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS部署脚本 - 使用Nuitka构建VidFlowDesktop
"""

import os
import sys
from app.common.config import VERSION

if sys.platform == "darwin":
    args = [
        'python3 -m nuitka',
        '--standalone',
        '--plugin-enable=pyqt5',
        '--include-qt-plugins=sensible',
        '--show-memory',
        '--show-progress',
        "--macos-create-app-bundle",
        "--assume-yes-for-downloads",
        "--macos-disable-console",
        f"--macos-app-version={VERSION}",
        "--macos-app-name=VidFlowDesktop",
        "--macos-app-icon=app/resource/images/logo.icns",
        "--copyright=VidFlowDesktop Team",
        '--output-dir=dist',
        'VidFlowDesktop.py',
    ]
else:
    print("This script is only for macOS")
    sys.exit(1)

os.system(' '.join(args))