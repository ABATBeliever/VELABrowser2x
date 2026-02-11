"""
VELA Browser - 定数・設定値・スタイルシート定義、およびその生成
"""

import sys
import platform
from pathlib import Path

# =====================================================================
# ブラウザ情報
# =====================================================================
BROWSER_NAME = "VELA"
BROWSER_CODENAME = "Praxis"
BROWSER_VERSION_SEMANTIC = "2.0.0.0"
BROWSER_VERSION_NAME = "2.0.0.0 Stable"
BROWSER_FULL_NAME = f"{BROWSER_NAME} {BROWSER_CODENAME} {BROWSER_VERSION_NAME}"

def detect_browser_target_architecture():
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "linux":
        if machine in ("x86_64", "amd64"):
            return "linux-x64"
        elif machine in ("aarch64", "arm64"):
            try:
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read().lower()
                if "raspberry pi" in cpuinfo:
                    return "rasp-a64"
            except Exception:
                pass
            return "linux-a64"
    elif system == "windows":
        if machine in ("arm64", "aarch64"):
            return "win-a64"
        return "win-x64"
    elif system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "mac-a64"
    return "win-x64"

BROWSER_TARGET_Architecture = detect_browser_target_architecture()

UPDATE_CHECK_URL = f"https://abatbeliever.net/upd/VELABrowser/{BROWSER_CODENAME}/{BROWSER_TARGET_Architecture}.updat"

# =====================================================================
# UserAgentプリセット
# =====================================================================
USER_AGENT_PRESETS = {
    0: "",  # デフォルト(Chromium)
    1: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
    2: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    3: "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.135 Mobile Safari/537.36",
    4: "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    5: ""  # カスタム(ユーザー設定から取得)
}

USER_AGENT_PRESET_NAMES = [
    "デフォルト (Chromium)",
    "Firefox 147 (Windows)",
    "Safari 16.5 (macOS)",
    "Chrome Mobile (Android)",
    "Safari Mobile (iOS)",
    "カスタム"
]

# =====================================================================
# データディレクトリ設定
# =====================================================================
DATA_DIR = Path.home() / ".VELA_Browser"
DATA_DIR.mkdir(exist_ok=True)

HISTORY_DB = DATA_DIR / "history.db"
SESSION_FILE = DATA_DIR / "session.json"
BOOKMARKS_DB = DATA_DIR / "bookmarks.db"
DOWNLOADS_DB = DATA_DIR / "downloads.db"
DOWNLOADS_DIR = DATA_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# =====================================================================
# スタイルシート定義
# =====================================================================

STYLES = {
    'main_window': """
        QMainWindow {
            background-color: #fafafa;
        }
    """,

    'toolbar': """
        QToolBar {
            background-color: #f3f4f6;
            border-bottom: 1px solid #dcdfe3;
            spacing: 6px;
            padding: 6px;
        }
        QPushButton {
            background-color: #ffffff;
            color: #2e2e2e;
            border: 1px solid #dcdfe3;
            border-radius: 4px;
            padding: 6px 8px;
        }
        QPushButton:hover {
            background-color: #eaf2fb;
            border-color: #4a90d9;
            color: #1f5fa5;
        }
        QPushButton:pressed {
            background-color: #d6e8fa;
        }
        QLineEdit {
            background-color: #ffffff;
            color: #2e2e2e;
            border: 1px solid #dcdfe3;
            border-radius: 4px;
            padding: 6px;
            font-size: 10pt;
            selection-background-color: #4a90d9;
            selection-color: #ffffff;
        }
        QLineEdit:focus {
            border: 2px solid #4a90d9;
        }
    """,

    'tab_list': """
        QWidget {
            background-color: #f5f6f8;
            border-right: 1px solid #dcdfe3;
        }
        QListWidget {
            background-color: #ffffff;
            border: 1px solid #dcdfe3;
            border-radius: 4px;
            outline: none;
        }
        QListWidget::item {
            padding: 12px;
            color: #2e2e2e;
            background-color: #ffffff;
        }
        QListWidget::item:hover {
            background-color: #f0f3f7;
        }
        QListWidget::item:selected {
            background-color: #eaf2fb;
            color: #1f5fa5;
        }
    """,

    'splitter': """
        QSplitter::handle {
            background-color: #dcdfe3;
            width: 1px;
        }
    """,

    'menu': """
        QMenu {
            background-color: #ffffff;
            border: 1px solid #dcdfe3;
            border-radius: 4px;
            padding: 4px;
        }
        QMenu::item {
            padding: 8px 30px 8px 10px;
            border-radius: 4px;
            color: #2e2e2e;
        }
        QMenu::item:selected {
            background-color: #eaf2fb;
            color: #1f5fa5;
        }
        QMenu::separator {
            height: 1px;
            background-color: #dcdfe3;
            margin: 4px 0px;
        }
    """,

    'dialog': """
        QDialog {
            background-color: #ffffff;
            color: #2e2e2e;
        }
        QLabel {
            color: #2e2e2e;
        }

        QLineEdit, QTextEdit {
            background-color: #ffffff;
            border: 1px solid #dcdfe3;
            border-radius: 4px;
            padding: 6px;
            selection-background-color: #4a90d9;
            selection-color: #ffffff;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 2px solid #4a90d9;
        }

        QComboBox {
            background-color: #ffffff;
            border: 1px solid #dcdfe3;
            border-radius: 4px;
            padding: 6px 28px 6px 6px;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 22px;
            border: none;
            background: transparent;
        }
        QComboBox::down-arrow {
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #5f6368;
        }
        QComboBox:hover {
            border-color: #4a90d9;
        }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            border: 1px solid #dcdfe3;
            selection-background-color: #eaf2fb;
            selection-color: #1f5fa5;
        }

        QGroupBox {
            border: 1px solid #dcdfe3;
            border-radius: 4px;
            margin-top: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 6px;
            background-color: #ffffff;
            font-weight: 600;
        }

        /* CheckBox / RadioButton */
        QCheckBox, QRadioButton {
            spacing: 6px;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #9aa0a6;
            border-radius: 4px;
            background-color: #ffffff;
        }
        QCheckBox::indicator:checked {
            background-color: #4a90d9;
            border-color: #4a90d9;
        }

        QRadioButton::indicator {
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid #9aa0a6;
            background-color: #ffffff;
        }
        QRadioButton::indicator:checked {
            border-color: #4a90d9;
            background-color: #4a90d9;
        }

        /* Table / Tree */
        QTableWidget, QTreeWidget {
            border: 1px solid #dcdfe3;
            alternate-background-color: #f7f9fc;
            gridline-color: #e2e5ea;
        }
        QTableWidget::item:selected, QTreeWidget::item:selected {
            background-color: #4a90d9;
            color: #ffffff;
        }
        QTableWidget::item:hover, QTreeWidget::item:hover {
            background-color: #eaf2fb;
        }

        QHeaderView::section {
            background-color: #f3f4f6;
            border: 1px solid #dcdfe3;
            padding: 6px;
            font-weight: 600;
        }

        /* ScrollBar */
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
        }
        QScrollBar::handle:vertical {
            background-color: rgba(120, 120, 120, 80);
            border-radius: 5px;
            min-height: 24px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: rgba(120, 120, 120, 140);
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QProgressBar {
            border: 1px solid #dcdfe3;
            border-radius: 4px;
            background-color: #f3f4f6;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4a90d9;
            border-radius: 3px;
        }
    """,

    'tab_widget': """
        QTabWidget::pane {
            border: 1px solid #dcdfe3;
            background-color: #ffffff;
        }
        QTabBar::tab {
            background-color: #f3f4f6;
            padding: 10px 20px;
            border: 1px solid #dcdfe3;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background-color: #ffffff;
            color: #4a90d9;
            border-bottom: 2px solid #4a90d9;
        }
        QTabBar::tab:hover {
            background-color: #eaf2fb;
        }
    """,

    'button_primary': """
        QPushButton {
            background-color: #4a90d9;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #3a7fc4;
        }
        QPushButton:pressed {
            background-color: #2f6ca8;
        }
    """,

    'button_secondary': """
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #dcdfe3;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #f0f3f7;
        }
        QPushButton:pressed {
            background-color: #e2e5ea;
        }
    """
}
