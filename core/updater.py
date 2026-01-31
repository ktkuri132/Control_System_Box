"""
自动更新模块
检查 GitHub Release 并下载更新
"""
import os
import sys
import json
import tempfile
import subprocess
from urllib.request import urlopen, Request
from urllib.error import URLError
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import (QMessageBox, QProgressDialog, QApplication)

# 配置
GITHUB_REPO = "ktkuri132/Control_System_Box"
CURRENT_VERSION = "2.1.2"  # ★ 当前版本号
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def is_frozen() -> bool:
    """
    检测是否为打包后的可执行文件
    支持 PyInstaller、Nuitka、cx_Freeze 等
    """
    # 方法1: PyInstaller 设置的 frozen 属性
    if getattr(sys, 'frozen', False):
        return True

    # 方法2: Nuitka 编译检测 - 检查 __compiled__ 模块
    try:
        import __compiled__
        return True
    except ImportError:
        pass

    # 方法3: 检查可执行文件名
    exe_path = sys.executable.lower()
    exe_name = os.path.basename(exe_path)

    # 如果是我们的程序名，肯定是打包后的
    if 'controlsystemtool' in exe_name:
        return True

    # 如果不是 python 解释器，也认为是打包后的
    if exe_path.endswith('.exe') and 'python' not in exe_name:
        return True

    return False


class VersionChecker(QThread):
    """版本检查线程"""
    update_available = pyqtSignal(str, str, str)  # 新版本号, 下载链接, 更新说明
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)  # 错误信息

    def run(self):
        try:
            req = Request(UPDATE_CHECK_URL, headers={'User-Agent': 'ControlSystemTool'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            latest_version = data.get('tag_name', '').lstrip('v')

            if self._is_newer_version(latest_version, CURRENT_VERSION):
                # 查找 exe 下载链接
                download_url = None
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.exe') and 'Setup' not in asset['name']:
                        download_url = asset['browser_download_url']
                        break

                if download_url:
                    release_notes = data.get('body', '暂无更新说明')
                    self.update_available.emit(latest_version, download_url, release_notes)
                else:
                    self.no_update.emit()
            else:
                self.no_update.emit()

        except URLError as e:
            self.check_failed.emit(f"网络错误: {str(e)}")
        except Exception as e:
            self.check_failed.emit(f"检查更新失败: {str(e)}")

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """比较版本号"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            return latest_parts > current_parts
        except:
            return False


class UpdateDownloader(QThread):
    """更新下载线程"""
    progress = pyqtSignal(int, int)  # 已下载, 总大小
    download_complete = pyqtSignal(str)  # 下载文件路径
    download_failed = pyqtSignal(str)  # 错误信息

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            req = Request(self.url, headers={'User-Agent': 'ControlSystemTool'})
            with urlopen(req, timeout=60) as response:
                total_size = int(response.headers.get('Content-Length', 0))

                # 创建临时文件
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, 'ControlSystemTool_new.exe')

                downloaded = 0
                chunk_size = 8192

                with open(temp_file, 'wb') as f:
                    while True:
                        if self._cancelled:
                            return

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)

                self.download_complete.emit(temp_file)

        except Exception as e:
            self.download_failed.emit(f"下载失败: {str(e)}")


class AutoUpdater(QObject):
    """自动更新管理器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.checker = None
        self.downloader = None
        self.progress_dialog = None

    def check_for_updates(self, silent=False):
        """
        检查更新
        :param silent: 静默模式，无更新时不显示提示
        """
        self.silent = silent
        self.checker = VersionChecker()
        self.checker.update_available.connect(self._on_update_available)
        self.checker.no_update.connect(self._on_no_update)
        self.checker.check_failed.connect(self._on_check_failed)
        self.checker.start()

    def _on_update_available(self, version: str, url: str, notes: str):
        """发现新版本"""
        msg = QMessageBox(self.parent_widget)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("发现新版本")
        msg.setText(f"发现新版本 v{version}，当前版本 v{CURRENT_VERSION}")
        msg.setDetailedText(notes)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.button(QMessageBox.StandardButton.Yes).setText("立即更新")
        msg.button(QMessageBox.StandardButton.No).setText("稍后提醒")

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self._start_download(url)

    def _on_no_update(self):
        """无更新"""
        if not self.silent:
            QMessageBox.information(
                self.parent_widget,
                "检查更新",
                f"当前已是最新版本 v{CURRENT_VERSION}"
            )

    def _on_check_failed(self, error: str):
        """检查失败"""
        if not self.silent:
            QMessageBox.warning(
                self.parent_widget,
                "检查更新",
                error
            )

    def _start_download(self, url: str):
        """开始下载"""
        self.progress_dialog = QProgressDialog(
            "正在下载更新...", "取消", 0, 100, self.parent_widget
        )
        self.progress_dialog.setWindowTitle("下载更新")
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.canceled.connect(self._cancel_download)

        self.downloader = UpdateDownloader(url)
        self.downloader.progress.connect(self._on_download_progress)
        self.downloader.download_complete.connect(self._on_download_complete)
        self.downloader.download_failed.connect(self._on_download_failed)
        self.downloader.start()

    def _cancel_download(self):
        """取消下载"""
        if self.downloader:
            self.downloader.cancel()

    def _on_download_progress(self, downloaded: int, total: int):
        """下载进度"""
        if total > 0:
            percent = int(downloaded * 100 / total)
            self.progress_dialog.setValue(percent)
            self.progress_dialog.setLabelText(
                f"正在下载更新... {downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB"
            )

    def _on_download_complete(self, file_path: str):
        """下载完成"""
        self.progress_dialog.close()

        msg = QMessageBox.question(
            self.parent_widget,
            "下载完成",
            "更新已下载完成，是否立即安装？\n程序将自动重启。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if msg == QMessageBox.StandardButton.Yes:
            self._install_update(file_path)

    def _on_download_failed(self, error: str):
        """下载失败"""
        self.progress_dialog.close()
        QMessageBox.critical(
            self.parent_widget,
            "下载失败",
            error
        )

    def _install_update(self, new_exe_path: str):
        """安装更新"""
        try:
            current_exe = sys.executable

            # 检测是否为打包后的 exe
            if is_frozen():
                # 创建更新脚本
                update_script = os.path.join(tempfile.gettempdir(), 'update.bat')

                with open(update_script, 'w', encoding='gbk') as f:
                    f.write(f'''@echo off
chcp 65001 >nul
echo 正在更新，请稍候...
timeout /t 2 /nobreak >nul
copy /y "{new_exe_path}" "{current_exe}"
if errorlevel 1 (
    echo 更新失败，请手动替换文件
    pause
    exit /b 1
)
del "{new_exe_path}"
echo 更新完成，正在重启程序...
start "" "{current_exe}"
del "%~f0"
''')

                # 运行更新脚本并退出当前程序
                subprocess.Popen(
                    ['cmd', '/c', update_script],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                QApplication.quit()
            else:
                # 开发模式，直接提示
                QMessageBox.information(
                    self.parent_widget,
                    "更新",
                    f"开发模式下不执行自动更新。\n新版本已下载到: {new_exe_path}"
                )

        except Exception as e:
            QMessageBox.critical(
                self.parent_widget,
                "更新失败",
                f"安装更新时出错: {str(e)}"
            )


def get_current_version() -> str:
    """获取当前版本号"""
    return CURRENT_VERSION
