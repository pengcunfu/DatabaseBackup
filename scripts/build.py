import os
import sys
from pathlib import Path

# 版本信息
VERSION = "1.0.0"
YEAR = "2025"
AUTHOR = "pengcunfu"

# 项目信息
PRODUCT_NAME = "Database Backup Tool"
COMPANY_NAME = "PyDatabaseBackup"
DESCRIPTION = "MySQL Database Backup and Synchronization Tool"
MAIN_FILE = "main.py"


def build_windows():
    """构建Windows版本"""
    args = [
        'nuitka',
        '--standalone',
        '--windows-console-mode=disable',
        '--plugin-enable=pyside6',
        '--assume-yes-for-downloads',
        '--msvc=latest',
        '--enable-plugin=pyside6',

        # 包含APScheduler相关模块
        '--include-package=apscheduler',
        '--include-package=tzlocal',

        # 包含项目app目录
        '--include-package=app',

        # 确保包含数据文件
        '--include-data-files=resources/config.yaml=resources/config.yaml',
        '--include-data-files=resources/icon.png=resources/icon.png',

        # Windows元数据
        '--windows-icon-from-ico=resources/icon.ico' if Path('resources/icon.ico').exists() else '',
        f'--company-name={COMPANY_NAME}',
        f'--product-name="{PRODUCT_NAME}"',
        f'--file-version={VERSION}',
        f'--product-version={VERSION}',
        f'--file-description="{DESCRIPTION}"',
        f'--copyright="Copyright(C) {YEAR} {AUTHOR}"',

        '--output-dir=dist',
        MAIN_FILE,
    ]

    # 过滤掉空字符串
    args = [arg for arg in args if arg]

    if "--onefile" in sys.argv:
        args.remove('--standalone')
        args.insert(1, "--onefile")
        args.insert(2, "--onefile-cache-mode=cached")

    return args


def build_macos():
    """构建macOS版本"""
    args = [
        'python3 -m nuitka',
        '--standalone',
        '--plugin-enable=pyside6',
        '--static-libpython=no',
        '--macos-create-app-bundle',
        '--assume-yes-for-downloads',
        '--macos-app-mode=gui',

        # 包含APScheduler相关模块
        '--include-package=apscheduler',
        '--include-package=tzlocal',

        # 包含项目app目录
        '--include-package=app',

        # 确保包含数据文件
        '--include-data-files=resources/config.yaml=resources/config.yaml',
        '--include-data-files=resources/icon.png=resources/icon.png',

        # macOS元数据
        f"--macos-app-version={VERSION}",
        "--macos-app-icon=resources/icon.icns" if Path('resources/icon.icns').exists() else '',
        f'--copyright="Copyright(C) {YEAR} {AUTHOR}"',

        '--output-dir=dist',
        MAIN_FILE,
    ]

    # 过滤掉空字符串
    args = [arg for arg in args if arg]

    return args


def build_linux():
    """构建Linux版本"""
    args = [
        'nuitka',
        '--standalone',
        '--plugin-enable=pyside6',
        '--include-qt-plugins=platforms',
        '--assume-yes-for-downloads',

        # 包含APScheduler相关模块
        '--include-package=apscheduler',
        '--include-package=tzlocal',

        # 包含项目app目录
        '--include-package=app',

        # 确保包含数据文件
        '--include-data-files=resources/config.yaml=resources/config.yaml',
        '--include-data-files=resources/icon.png=resources/icon.png',

        '--linux-icon=resources/icon.png' if Path('resources/icon.png').exists() else '',
        '--output-dir=dist',
        MAIN_FILE,
    ]

    # 过滤掉空字符串
    args = [arg for arg in args if arg]

    return args


def main():
    """主构建函数"""
    if sys.platform == "win32":
        args = build_windows()
    elif sys.platform == "darwin":
        args = build_macos()
    else:
        args = build_linux()

    print("Build command:")
    print(' '.join(args))
    print("\nStarting build...")

    # 执行构建
    cmd = ' '.join(args)
    exit_code = os.system(cmd)

    if exit_code == 0:
        print(f"\nBuild successful! Output directory: dist/")
    else:
        print(f"\nBuild failed! Error code: {exit_code}")
        sys.exit(1)


if __name__ == "__main__":
    main()