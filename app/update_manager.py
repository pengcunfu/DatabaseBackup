"""
版本更新管理器
功能：检查更新、下载更新、安装更新
"""
import os
import sys
import json
import urllib.request
import urllib.error
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QMessageBox, QApplication


class UpdateChecker(QThread):
    """更新检查线程"""

    # 信号
    check_complete = Signal(dict)  # 检查完成，传递更新信息
    check_failed = Signal(str)  # 检查失败
    download_progress = Signal(int, int)  # 下载进度 (current, total)
    download_complete = Signal(str)  # 下载完成，传递文件路径
    download_failed = Signal(str)  # 下载失败

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_version = "1.0.0"
        self.repo_url = "https://api.github.com/repos/pengcunfu/DatabaseBackup/releases/latest"
        self.update_url = "https://github.com/pengcunfu/DatabaseBackup/releases/download"
        self.download_path = None

    def set_current_version(self, version: str):
        """设置当前版本号"""
        self.current_version = version

    def check_for_updates(self):
        """检查是否有新版本"""
        """检查更新"""
        try:
            # 创建请求
            req = urllib.request.Request(
                self.repo_url,
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )

            # 发送请求
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            # 解析版本信息
            latest_version = data.get('tag_name', '').lstrip('v')
            release_notes = data.get('body', '')
            download_url = None
            file_size = 0

            # 查找Windows安装程序
            for asset in data.get('assets', []):
                name = asset.get('name', '')
                if name.endswith('.exe') and 'Setup' in name:
                    download_url = asset.get('browser_download_url')
                    file_size = asset.get('size', 0)
                    break

            update_info = {
                'has_update': self._compare_version(latest_version, self.current_version),
                'current_version': self.current_version,
                'latest_version': latest_version,
                'release_notes': release_notes,
                'download_url': download_url,
                'file_size': file_size,
                'release_url': data.get('html_url', ''),
            }

            self.check_complete.emit(update_info)

        except urllib.error.URLError as e:
            self.check_failed.emit(f"网络错误: {str(e)}")
        except json.JSONDecodeError:
            self.check_failed.emit("解析更新信息失败")
        except Exception as e:
            self.check_failed.emit(f"检查更新失败: {str(e)}")

    def _compare_version(self, latest: str, current: str) -> bool:
        """比较版本号"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]

            # 补齐版本号位数
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return latest_parts > current_parts
        except (ValueError, AttributeError):
            return False

    def download_update(self, url: str, save_path: str):
        """下载更新"""
        try:
            # 创建临时目录
            temp_dir = Path(save_path).parent
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 下载文件
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            with urllib.request.urlopen(req) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192

                with open(save_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.download_progress.emit(downloaded, total_size)

            self.download_complete.emit(save_path)

        except urllib.error.URLError as e:
            self.download_failed.emit(f"下载失败: {str(e)}")
        except Exception as e:
            self.download_failed.emit(f"下载错误: {str(e)}")

    def run(self):
        """线程运行"""
        self.check_for_updates()


class UpdateManager(QObject):
    """更新管理器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checker = UpdateChecker()
        self._setup_connections()

    def _setup_connections(self):
        """设置信号连接"""
        self.checker.check_complete.connect(self._on_check_complete)
        self.checker.check_failed.connect(self._on_check_failed)
        self.checker.download_progress.connect(self._on_download_progress)
        self.checker.download_complete.connect(self._on_download_complete)
        self.checker.download_failed.connect(self._on_download_failed)

    def check_for_updates(self, current_version: str):
        """检查更新"""
        self.checker.set_current_version(current_version)
        self.checker.start()

    def _on_check_complete(self, update_info: Dict[str, Any]):
        """检查完成处理"""
        if update_info['has_update']:
            self._show_update_dialog(update_info)
        else:
            QMessageBox.information(
                None,
                "检查更新",
                f"当前已是最新版本！\n\n当前版本: {update_info['current_version']}\n最新版本: {update_info['latest_version']}"
            )

    def _on_check_failed(self, error: str):
        """检查失败处理"""
        QMessageBox.warning(None, "检查更新失败", error)

    def _show_update_dialog(self, update_info: Dict[str, Any]):
        """显示更新对话框"""
        current = update_info['current_version']
        latest = update_info['latest_version']
        notes = update_info.get('release_notes', '暂无更新说明')
        size_mb = update_info.get('file_size', 0) / (1024 * 1024)

        msg = QMessageBox()
        msg.setWindowTitle("发现新版本")
        msg.setText(f"发现新版本！\n\n当前版本: {current}\n最新版本: {latest}\n安装包大小: {size_mb:.1f} MB")
        msg.setDetailedText(notes)

        # 添加按钮
        download_button = msg.addButton("下载更新", QMessageBox.ActionRole)
        later_button = msg.addButton("稍后提醒", QMessageBox.ActionRole)
        skip_button = msg.addButton("跳过此版本", QMessageBox.ActionRole)

        msg.exec_()

        if msg.clickedButton() == download_button:
            self._download_update(update_info)
        elif msg.clickedButton() == skip_button:
            pass  # 可以保存跳过的版本号

    def _download_update(self, update_info: Dict[str, Any]):
        """下载更新"""
        url = update_info.get('download_url')
        if not url:
            QMessageBox.warning(None, "下载失败", "未找到下载链接")
            return

        # 保存路径
        temp_dir = Path.home() / "Downloads"
        filename = f"DatabaseBackup-Setup-{update_info['latest_version']}.exe"
        save_path = temp_dir / filename

        # 显示下载进度对话框
        QMessageBox.information(
            None,
            "开始下载",
            f"正在下载更新到:\n{save_path}\n\n请稍候..."
        )

        # 启动下载
        self.checker.download_update(url, str(save_path))

    def _on_download_progress(self, current: int, total: int):
        """下载进度处理"""
        if total > 0:
            progress = (current / total) * 100
            print(f"\r下载进度: {progress:.1f}%", end='', flush=True)

    def _on_download_complete(self, file_path: str):
        """下载完成处理"""
        print("\n下载完成！")

        msg = QMessageBox()
        msg.setWindowTitle("下载完成")
        msg.setText(f"更新已下载完成！\n\n保存位置: {file_path}")
        msg.setInformativeText("是否现在安装更新？")

        install_button = msg.addButton("立即安装", QMessageBox.ActionRole)
        later_button = msg.addButton("稍后安装", QMessageBox.ActionRole)

        msg.exec_()

        if msg.clickedButton() == install_button:
            # 启动安装程序
            self._install_update(file_path)

    def _on_download_failed(self, error: str):
        """下载失败处理"""
        QMessageBox.critical(None, "下载失败", error)

    def _install_update(self, installer_path: str):
        """安装更新"""
        try:
            # 启动安装程序
            if sys.platform == "win32":
                os.startfile(installer_path)
            else:
                os.system(f'open "{installer_path}"')

            # 退出当前程序
            QApplication.quit()

        except Exception as e:
            QMessageBox.critical(
                None,
                "安装失败",
                f"无法启动安装程序:\n{str(e)}\n\n请手动运行安装程序。"
            )


def get_current_version() -> str:
    """获取当前版本号"""
    # 从配置文件或常量读取版本号
    try:
        # 尝试从 build.py 读取
        build_py = Path(__file__).parent.parent / "scripts" / "build.py"
        if build_py.exists():
            content = build_py.read_text(encoding='utf-8')
            import re
            match = re.search(r'VERSION\s*=\s*["\']([\d.]+)["\']', content)
            if match:
                return match.group(1)
    except Exception:
        pass

    # 默认版本号
    return "1.0.0"


# 便捷函数
def check_update(parent=None):
    """检查更新（便捷函数）"""
    manager = UpdateManager(parent)
    current_version = get_current_version()
    manager.check_for_updates(current_version)
    return manager


if __name__ == "__main__":
    # 测试代码
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    manager = check_update()
    sys.exit(app.exec())
