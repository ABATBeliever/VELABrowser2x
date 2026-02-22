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
BROWSER_VERSION_SEMANTIC = "2.1.0.0"
BROWSER_VERSION_NAME = "2.1.0.0 Stable"
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
# データディレクトリ設定（XDG準拠）
# =====================================================================

def _get_xdg_dirs():
    """
    OS に応じた XDG ベースディレクトリを返す。
      Linux  : XDG 標準 (~/.config, ~/.local/share, ~/.cache, ~/.local/state)
      Windows: 独自マッピング (~/.config, ~/.local/share, ~/.local/cache, ~/.local/state)
      その他 : 旧来の ~/.VELA_Browser に統合（変更なし）
    戻り値: (config_home, data_home, cache_home, state_home)
    """
    system = platform.system().lower()
    home = Path.home()

    if system == "linux":
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        data_home   = Path(os.environ.get("XDG_DATA_HOME",   home / ".local" / "share"))
        cache_home  = Path(os.environ.get("XDG_CACHE_HOME",  home / ".cache"))
        state_home  = Path(os.environ.get("XDG_STATE_HOME",  home / ".local" / "state"))
    elif system == "windows":
        config_home = home / ".config"
        data_home   = home / ".local" / "share"
        cache_home  = home / ".local" / "cache"
        state_home  = home / ".local" / "state"
    else:
        # macOS その他は旧来ディレクトリに統合して変更なし
        legacy = home / ".VELA_Browser"
        return legacy, legacy, legacy, legacy

    return config_home, data_home, cache_home, state_home

import os as _os_module  # os は後で使う。先に取り込んでおく
import os

_config_home, _data_home, _cache_home, _state_home = _get_xdg_dirs()

# VELA 専用サブディレクトリ
_VELA_APP_NAME = "VELABrowser"

# 設定・DB は config/data/state に分離
CONFIG_DIR  = _config_home / _VELA_APP_NAME   # 設定（将来的に ini など）
DATA_DIR    = _data_home   / _VELA_APP_NAME   # DB・ブックマーク・セッション
CACHE_DIR   = _cache_home  / _VELA_APP_NAME   # WebEngine キャッシュ
STATE_DIR   = _state_home  / _VELA_APP_NAME   # WebEngine 永続ストレージ

for _d in (CONFIG_DIR, DATA_DIR, CACHE_DIR, STATE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# 旧来パス（移行元の検出に使用）
LEGACY_DATA_DIR = Path.home() / ".VELA_Browser"

HISTORY_DB    = DATA_DIR / "history.db"
SESSION_FILE  = DATA_DIR / "session.json"
BOOKMARKS_DB  = DATA_DIR / "bookmarks.db"
DOWNLOADS_DB  = DATA_DIR / "downloads.db"
DOWNLOADS_DIR = DATA_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# WebEngine プロファイルパス
PROFILE_PATH         = STATE_DIR / "profile"
INCOGNITO_CACHE_PATH = CACHE_DIR / "incognito"
INCOGNITO_STATE_PATH = STATE_DIR / "incognito_storage"

# =====================================================================
# バージョンスタンプ（DB / JSON への埋め込みと検証）
# =====================================================================

VERSION_KEY = "_vela_version"

def stamp_version_to_json(data: dict) -> dict:
    """JSON データにバージョンスタンプを付与して返す"""
    data[VERSION_KEY] = BROWSER_VERSION_SEMANTIC
    return data

def check_version_stamp(data: dict, source_label: str = "") -> bool:
    """
    data に埋め込まれたバージョンが現在のバージョンより *新しい* 場合 False を返す。
    バージョンが記録されていない・同じ・古い場合は True を返す。
    呼び出し元は False の場合に警告を表示すること。
    """
    from packaging import version as _ver
    stamped = data.get(VERSION_KEY, "")
    if not stamped:
        return True  # スタンプなし＝旧データ、問題なし
    try:
        if _ver.parse(stamped) > _ver.parse(BROWSER_VERSION_SEMANTIC):
            print(f"[WARN] {source_label}: データは新しいVELA ({stamped}) で書かれています")
            return False
    except Exception:
        pass
    return True

def get_db_vela_version(db_path) -> str:
    """
    SQLite DB の meta テーブルから VELA バージョンを取得する。
    テーブルが存在しない・取得失敗の場合は空文字を返す。
    """
    import sqlite3
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM meta WHERE key = ?", (VERSION_KEY,))
            row = cur.fetchone()
            return row[0] if row else ""
    except Exception:
        return ""

def set_db_vela_version(conn):
    """
    SQLite 接続に対して meta テーブルを作成し、バージョンを書き込む。
    既存接続に対して呼ぶこと（commit は呼び出し元が行う）。
    """
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cur.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        (VERSION_KEY, BROWSER_VERSION_SEMANTIC)
    )

def check_db_version(db_path, label: str = "") -> bool:
    """
    DB に記録されているバージョンと現在のバージョンを比較する。
    現在より新しければ False、問題なければ True。
    """
    from packaging import version as _ver
    stamped = get_db_vela_version(db_path)
    if not stamped:
        return True
    try:
        if _ver.parse(stamped) > _ver.parse(BROWSER_VERSION_SEMANTIC):
            print(f"[WARN] {label}: DB は新しいVELA ({stamped}) で書かれています")
            return False
    except Exception:
        pass
    return True

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
            padding: 0px;
            margin: 2px;
            color: #2e2e2e;
            background-color: #ffffff;
            border-radius: 4px;
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
    """,    
    'tab_item_close_button': """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 3px;
            padding: 2px;
            min-width: 16px;
            max-width: 16px;
            min-height: 16px;
            max-height: 16px;
        }
        QPushButton:hover {
            background-color: rgba(0, 0, 0, 0.1);
        }
        QPushButton:pressed {
            background-color: rgba(0, 0, 0, 0.2);
        }
    """,
    
    'tab_context_menu': """
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

    # シークレットタブ用のラベルスタイル
    'incognito_title_label': """
        QLabel {
            background: transparent;
            color: #8a2be2;
            padding: 0px;
            font-size: 10pt;
        }
    """,

    # ロード進捗バー（URLバー下部）
    'load_progress_bar': """
        QProgressBar {
            border: none;
            border-radius: 0px;
            background-color: transparent;
            max-height: 3px;
            min-height: 3px;
        }
        QProgressBar::chunk {
            background-color: #4a90d9;
            border-radius: 0px;
        }
    """
}
