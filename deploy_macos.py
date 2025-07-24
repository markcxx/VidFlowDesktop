#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS部署脚本 - 使用Nuitka构建VidFlowDesktop
"""

import os
import sys

if sys.platform == "darwin":
    args = [
        'python3 -m nuitka',
        '--standalone',
        '--plugin-enable=pyqt5',
        '--include-qt-plugins=sensible,styles',
        '--show-memory',
        '--show-progress',
        '--assume-yes-for-downloads',
        '--deployment',
        "--macos-create-app-bundle",
        "--macos-disable-console",
        "--macos-app-version=1.0.0",
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