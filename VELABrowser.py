"""
 *
 * VELA Browser
 * Copyright (C) 2025-2026 ABATBeliever
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>
 *
 * For description, please watch "LICENSE" file.
 *
"""

# =====================================================================
# このファイルは constants.py を内包しています（2.1.2.0 以降）
# constants モジュールとして他ファイルから import 可能にするため、
# sys.modules に自分自身を "constants" として登録します。
# =====================================================================

import sys
import os
import shutil
import platform
import logging
from pathlib import Path

# =====================================================================
# ブラウザ情報
# =====================================================================

BROWSER_NAME = "VELA"
BROWSER_CODENAME = "Praxis"
BROWSER_VERSION_SEMANTIC = "2.1.2.1"
BROWSER_VERSION_NAME = "2.1.2.1"
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

UPDATE_CHECK_URL = (
    f"https://abatbeliever.net/upd/VELABrowser/"
    f"{BROWSER_CODENAME}/{BROWSER_TARGET_Architecture}.updat"
)

# =====================================================================
# 開発者向けフラグ
# =====================================================================

# アップデート確認を行うかどうか（False にすると起動時チェックをスキップ）
CHECK_FOR_UPDATES: bool = True

# =====================================================================
# UserAgentプリセット
# =====================================================================

USER_AGENT_PRESETS = {
    0: "",  # デフォルト(Chromium)
    1: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
    2: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    3: "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.135 Mobile Safari/537.36",
    4: "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    5: ""   # カスタム(ユーザー設定から取得)
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
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config")))
        data_home   = Path(os.environ.get("XDG_DATA_HOME",   str(home / ".local" / "share")))
        cache_home  = Path(os.environ.get("XDG_CACHE_HOME",  str(home / ".cache")))
        state_home  = Path(os.environ.get("XDG_STATE_HOME",  str(home / ".local" / "state")))
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


_config_home, _data_home, _cache_home, _state_home = _get_xdg_dirs()

# VELA 専用サブディレクトリ
_VELA_APP_NAME = "VELABrowser"

CONFIG_DIR  = _config_home / _VELA_APP_NAME
DATA_DIR    = _data_home   / _VELA_APP_NAME
CACHE_DIR   = _cache_home  / _VELA_APP_NAME
STATE_DIR   = _state_home  / _VELA_APP_NAME

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
# ロガー設定
# =====================================================================
# ログファイルの出力先:
#   Linux  : $XDG_STATE_HOME/VELABrowser/vela.log
#   Windows: ~/.local/state/VELABrowser/vela.log
#   その他 : ~/.VELA_Browser/vela.log
# 起動のたびにログファイルは上書き（mode='w'）する。
# =====================================================================

LOG_FILE = STATE_DIR / "vela.log"


def _setup_logger() -> logging.Logger:
    """
    print() と同時にファイルにも書き出すロガーを構築する。
    - コンソールハンドラ : StreamHandler(sys.stdout)
    - ファイルハンドラ   : FileHandler(LOG_FILE, mode='w') — 起動時に上書き
    フォーマット: [HH:MM:SS] message
    """
    _logger = logging.getLogger("VELA")
    _logger.setLevel(logging.DEBUG)
    # 重複ハンドラ防止
    if _logger.handlers:
        return _logger

    fmt = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(fmt)
    _logger.addHandler(ch)

    try:
        fh = logging.FileHandler(str(LOG_FILE), mode='w', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        _logger.addHandler(fh)
    except OSError as e:
        _logger.warning(f"ログファイルを開けません: {e}")

    return _logger


logger = _setup_logger()


def _vela_print(*args, **kwargs):
    """
    builtins.print を置き換えるラッパー。
    メッセージ先頭の [ERROR] / [WARN] を検出してログレベルを振り分ける。
    end/flush など logging に不要な kwargs は無視する。
    """
    msg = " ".join(str(a) for a in args)
    upper = msg.upper()
    if upper.startswith("[ERROR]"):
        logger.error(msg)
    elif upper.startswith("[WARN]"):
        logger.warning(msg)
    else:
        logger.info(msg)


# builtins.print を置き換えて全モジュールのログをキャプチャする
import builtins as _builtins
_builtins.print = _vela_print  # type: ignore[assignment]


# =====================================================================
# バージョンスタンプ（DB / JSON への埋め込みと検証）
# =====================================================================

VERSION_KEY = "_vela_version"


def stamp_version_to_json(data: dict) -> dict:
    """JSON データにバージョンスタンプを付与して返す"""
    data[VERSION_KEY] = BROWSER_VERSION_SEMANTIC
    return data


def check_version_stamp(data: dict, source_label: str = "") -> bool:
    from packaging import version as _ver
    stamped = data.get(VERSION_KEY, "")
    if not stamped:
        return True
    try:
        if _ver.parse(stamped) > _ver.parse(BROWSER_VERSION_SEMANTIC):
            print(f"[WARN] {source_label}: データは新しいVELA ({stamped}) で書かれています")
            return False
    except Exception:
        pass
    return True


def get_db_vela_version(db_path) -> str:
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
# スタイルシート定義（旧 constants.py より統合）
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

    'incognito_title_label': """
        QLabel {
            background: transparent;
            color: #8a2be2;
            padding: 0px;
            font-size: 10pt;
        }
    """,

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


# =====================================================================
# sys.modules への自己登録（他モジュールが "from constants import ..." できるようにする）
# =====================================================================

sys.modules.setdefault("constants", sys.modules[__name__])


# =====================================================================
# 起動前チェック: バージョン整合性
# =====================================================================

def _check_data_version_conflicts(app) -> bool:
    import json
    from PySide6.QtWidgets import QMessageBox

    newer_sources = []

    for db_path, label in [
        (HISTORY_DB,   "閲覧履歴 (history.db)"),
        (BOOKMARKS_DB, "ブックマーク (bookmarks.db)"),
        (DOWNLOADS_DB, "ダウンロード (downloads.db)"),
    ]:
        if db_path.exists() and not check_db_version(db_path, label):
            newer_sources.append((label, get_db_vela_version(db_path)))

    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                sess = json.load(f)
            if not check_version_stamp(sess, "session.json"):
                newer_sources.append(("セッション (session.json)", sess.get(VERSION_KEY, "不明")))
        except Exception:
            pass

    if not newer_sources:
        return True

    detail_lines = "\n".join(f"  • {label}（バージョン {ver}）" for label, ver in newer_sources)
    msg = QMessageBox()
    msg.setWindowTitle("データバージョンの警告")
    msg.setIcon(QMessageBox.Warning)
    msg.setText(
        f"以下のデータは、現在のVELA ({BROWSER_VERSION_SEMANTIC}) より\n"
        f"新しいバージョンで保存されています。\n\n"
        f"{detail_lines}\n\n"
        f"このまま起動すると、データが失われたり\n"
        f"正しく読み込めない可能性があります。\n"
        f"開発元は、この動作に対しデータの保証を行えません。"
    )
    msg.setInformativeText("起動しますか？")
    continue_btn = msg.addButton("無視して続行", QMessageBox.AcceptRole)
    abort_btn    = msg.addButton("起動しない(推奨)", QMessageBox.RejectRole)
    msg.setDefaultButton(abort_btn)
    msg.exec()

    return msg.clickedButton() == continue_btn


# =====================================================================
# 起動前チェック: XDG 移行
# =====================================================================

def _run_migration_if_needed(app) -> bool:
    from PySide6.QtWidgets import QMessageBox

    system = platform.system().lower()
    if system not in ("linux", "windows"):
        return True

    xdg_has_data = any([
        HISTORY_DB.exists(),
        BOOKMARKS_DB.exists(),
        SESSION_FILE.exists(),
        DOWNLOADS_DB.exists(),
    ])
    if xdg_has_data:
        return True

    if not LEGACY_DATA_DIR.exists():
        return True

    legacy_has_data = any([
        (LEGACY_DATA_DIR / "history.db").exists(),
        (LEGACY_DATA_DIR / "bookmarks.db").exists(),
        (LEGACY_DATA_DIR / "session.json").exists(),
        (LEGACY_DATA_DIR / "downloads.db").exists(),
    ])
    if not legacy_has_data:
        return True

    msg = QMessageBox()
    msg.setWindowTitle("データの移行")
    msg.setIcon(QMessageBox.Information)
    msg.setText(
        "旧バージョンのVELAのデータが見つかりました。\n\n"
        f"現在のパス\t:\n  {LEGACY_DATA_DIR}\n\n"
        f"XDGのパス\t:\n  {DATA_DIR}\n\n"
        "2.1.xのVELAを利用するには、データを新しい場所に移動する必要があります。\n"
        "※1 移行後にVELAを再起動してください。\n"
        "※2 移行をしても古いデータは削除されません。移行処理を行った段階でプロファイルが分岐します。"
    )
    migrate_btn = msg.addButton("移行する", QMessageBox.AcceptRole)
    cancel_btn  = msg.addButton("何もせず終了", QMessageBox.RejectRole)
    msg.setDefaultButton(migrate_btn)
    msg.exec()

    if msg.clickedButton() != migrate_btn:
        print("[INFO] Migration cancelled by user")
        return False

    _MIGRATE_FILES = [
        "history.db", "bookmarks.db", "downloads.db",
        "session.json", "downloads",
    ]
    errors = []
    for name in _MIGRATE_FILES:
        src = LEGACY_DATA_DIR / name
        if not src.exists():
            continue
        dst = DATA_DIR / name
        try:
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            print(f"[INFO] Migration: copied {name}")
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"[ERROR] Migration failed for {name}: {e}")

    if errors:
        err_text = "\n".join(errors)
        QMessageBox.warning(
            None, "エラー",
            f"一部のファイルの移行に失敗しました:\n{err_text}\n\nVELAを再起動してください。"
        )
    else:
        QMessageBox.information(
            None, "移行完了",
            f"データの移行が完了しました。\n\n"
            f"XDGのパス\t:\n  {DATA_DIR}\n\n"
            f"VELAを再起動してください。\n"
            f"※1 旧データは {LEGACY_DATA_DIR} に残りますが、2.0.xで今後行った変更は新たに移行をしない限り2.1.xでは表示されません\n。"
            f"※2 2.0.xの利用は今後推奨されません。"
        )

    print("[INFO] Migration complete. Restart required.")
    return False


# =====================================================================
# 起動前チェック: session.json 旧形式の自動変換
# =====================================================================

def _upgrade_session_if_needed(app) -> bool:
    from PySide6.QtWidgets import QMessageBox
    from managers import SessionManager
    mgr = SessionManager()
    status, data = mgr.load_session()

    if status == "converted":
        mgr.save_session(data)
        QMessageBox.information(
            None,
            "セッションデータの最適化",
            "セッションファイルを最適化しました。\n\nVELAを再起動してください。"
        )
        print("[INFO] Session converted to new format. Restart required.")
        return False

    return True


# =====================================================================
# メイン
# =====================================================================

def main():
    """アプリケーションのメイン関数"""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont

    # ---- Chromium フラグを QApplication 生成前に適用 ----
    # sys.argv への追加は QApplication(sys.argv) より前に行う必要がある
    from browser import apply_chromium_flags_from_settings
    apply_chromium_flags_from_settings()

    # ---- ヘッダーをコンソール／ログに出力 ----
    print(f"\n{BROWSER_FULL_NAME}")
    print("\nCopyright (C) 2025-2026 ABATBeliever")
    print("VELA Website     | https://abatbeliever.net/app/VELABrowser/")
    print("VELA Github Repo | https://github.com/ABATBeliever/VELABrowser2x")
    print(f"[INFO] Data Directory : {DATA_DIR}")
    print(f"[INFO] Log File       : {LOG_FILE}")

    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            background-color: #ffffff;
            color: #333333;
        }
        QMessageBox {
            background-color: #ffffff;
            color: #333333;
        }
        QMessageBox QLabel {
            color: #333333;
        }
        QMessageBox QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 6px 16px;
            border-radius: 4px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #106ebe;
        }
        QFileDialog {
            background-color: #ffffff;
            color: #333333;
        }
        QFileDialog QLabel {
            color: #333333;
        }
        QFileDialog QPushButton {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #e0e0e0;
            padding: 6px 16px;
            border-radius: 4px;
        }
        QFileDialog QTreeView, QFileDialog QListView {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #e0e0e0;
        }
        QFileDialog QTreeView::item, QFileDialog QListView::item {
            color: #333333;
        }
        QFileDialog QTreeView::item:selected, QFileDialog QListView::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        QToolTip {
            background-color: #333333;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px;
        }
    """)

    font = QFont()
    font.setPointSize(8)
    app.setFont(font)

    # ---- 起動前チェック（順番に実行、False で中断） ----

    if not _run_migration_if_needed(app):
        sys.exit(0)

    if not _upgrade_session_if_needed(app):
        sys.exit(0)

    if not _check_data_version_conflicts(app):
        sys.exit(0)

    # ---- ブラウザ起動 ----
    from browser import VerticalTabBrowser
    browser = VerticalTabBrowser()
    browser.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
