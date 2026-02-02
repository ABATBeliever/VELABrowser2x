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

import sys
import re
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import urlopen
from urllib.error import URLError
from packaging import version
from html import escape, unescape

from PySide6.QtCore import Qt, QUrl, Signal, QThread, QSettings
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLineEdit, QListWidget,
    QListWidgetItem, QSplitter, QToolBar, QDialog,
    QTabWidget, QLabel, QTextEdit, QFrame, QMessageBox,
    QCheckBox, QSpinBox, QComboBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QScrollArea, QFormLayout
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings, QWebEngineDownloadRequest
from PySide6.QtGui import QIcon, QAction, QFont, QPalette
import qtawesome as qta

# =====================================================================
# ブラウザ情報
# =====================================================================
BROWSER_NAME = "VELA"
BROWSER_CODENAME = "Praxis"
BROWSER_VERSION_SEMANTIC = "2.0.0.0a7"
BROWSER_VERSION_NAME = "2.0.0.0 Alpha7"
BROWSER_FULL_NAME = f"{BROWSER_NAME} {BROWSER_CODENAME} {BROWSER_VERSION_NAME}"
BROWSER_TARGET_Architecture = "win-x64"# linux-x64 / linux-a64 / rasp-a64 / win-x64 / win-a64 / mac-a64

UPDATE_CHECK_URL = f"https://abatbeliever.net/upd/VELABrowser/{BROWSER_CODENAME}/{BROWSER_TARGET_Architecture}.updat"

# =====================================================================
# データディレクトリ設定
# =====================================================================
DATA_DIR = Path.home() / ".vela_browser"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_DB = DATA_DIR / "history.db"
SESSION_FILE = DATA_DIR / "session.json"
BOOKMARKS_DB = DATA_DIR / "bookmarks.db"
DOWNLOADS_DIR = DATA_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

print(BROWSER_FULL_NAME)
print("\nCopyright (C) 2025-2026 ABATBeliever")
print(f"Data Directory: {DATA_DIR}")

# =====================================================================
# スタイルシート定義（統合）
# =====================================================================
STYLES = {
    'main_window': """
        QMainWindow{background-color:#fff}
    """,
    
    'toolbar': """
        QToolBar{background-color:#f5f5f5;border-bottom:1px solid #e0e0e0;spacing:5px;padding:5px}
        QPushButton{background-color:#fff;color:#333;border:1px solid #e0e0e0;border-radius:4px;padding:6px}
        QPushButton:hover{background-color:#e6f2ff;border-color:#0078d4}
        QPushButton:pressed{background-color:#cce4ff}
        QLineEdit{background-color:#fff;color:#333;border:1px solid #e0e0e0;border-radius:4px;padding:6px;font-size:10pt}
        QLineEdit:focus{border-color:#0078d4}
    """,
    
    'tab_list': """
        QWidget{background-color:#f9f9f9;border-right:1px solid #e0e0e0}
        QPushButton{background-color:#fff;color:#333;border:1px solid #e0e0e0;border-radius:4px}
        QPushButton:hover{background-color:#e6f2ff;border-color:#0078d4}
        QPushButton:pressed{background-color:#cce4ff}
        QListWidget{background-color:#fff;color:#333;border:1px solid #e0e0e0;border-radius:4px;outline:none}
        QListWidget::item{padding:12px;border-bottom:1px solid #f0f0f0;color:#333}
        QListWidget::item:selected{background-color:#e6f2ff;color:#0078d4}
        QListWidget::item:hover{background-color:#f5f5f5}
    """,
    
    'splitter': """
        QSplitter::handle {background-color: #e0e0e0;width: 1px;}
    """,
    
    'dialog': """
        QDialog{background-color:#fff}
        QLabel{color:#333}
        QLineEdit,QTextEdit,QComboBox{background-color:#fff;color:#333;border:1px solid #e0e0e0;border-radius:4px;padding:6px}
        QTableWidget,QTreeWidget{background-color:#fff;color:#333;border:1px solid #e0e0e0}
        QTableWidget::item,QTreeWidget::item{color:#333}
        QHeaderView::section{background-color:#f5f5f5;color:#333;padding:5px;border:1px solid #e0e0e0}
        QGroupBox{color:#333;border:1px solid #e0e0e0;border-radius:4px;margin-top:10px;padding-top:10px}
        QGroupBox::title{color:#333;subcontrol-origin:margin;left:10px;padding:0 5px}
        QCheckBox,QRadioButton{color:#333}
    """,
    
    'tab_widget': """
        QTabWidget::pane{border:1px solid #ccc;background:#fff}
        QTabBar::tab{background:#f0f0f0;color:#333;padding:10px 20px;margin-right:2px}
        QTabBar::tab:selected{background:#fff;border-bottom:2px solid #0078d4}
    """,
    
    'button_primary': """
        QPushButton{background-color:#0078d4;color:#fff;border:none;padding:8px 16px;border-radius:4px;font-size:11pt}
        QPushButton:hover{background-color:#106ebe}
        QPushButton:pressed{background-color:#005a9e}
    """,
    
    'button_secondary': """
        QPushButton{background-color:#fff;color:#333;border:1px solid #e0e0e0;padding:8px 16px;border-radius:4px}
        QPushButton:hover{background-color:#f5f5f5}
    """
}


# =====================================================================
# データ管理クラス群
# =====================================================================

class HistoryManager:
    """履歴管理クラス"""
    
    def __init__(self):
        self.db_path = HISTORY_DB
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                visit_count INTEGER DEFAULT 1
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON history(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_visit_time ON history(visit_time DESC)')
        conn.commit()
        conn.close()
        print("[INFO] History database initialized")
    
    def add_history(self, url, title):
        if not url or url.startswith("about:") or url.startswith("chrome:"):
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, visit_count FROM history WHERE url = ?', (url,))
        result = cursor.fetchone()
        
        if result:
            cursor.execute('''
                UPDATE history 
                SET title = ?, visit_time = CURRENT_TIMESTAMP, visit_count = ?
                WHERE id = ?
            ''', (title, result[1] + 1, result[0]))
        else:
            cursor.execute('INSERT INTO history (url, title) VALUES (?, ?)', (url, title))
        
        conn.commit()
        conn.close()
    
    def get_history(self, limit=100):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT url, title, visit_time, visit_count 
            FROM history 
            ORDER BY visit_time DESC 
            LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def search_history(self, query, limit=50):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT url, title, visit_time, visit_count 
            FROM history 
            WHERE url LIKE ? OR title LIKE ?
            ORDER BY visit_time DESC 
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def clear_history(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM history')
        conn.commit()
        conn.close()
        print("[INFO] History cleared")


class BookmarkManager:
    """ブックマーク管理クラス"""
    
    def __init__(self):
        self.db_path = BOOKMARKS_DB
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                folder TEXT DEFAULT 'root',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("[INFO] Bookmarks database initialized")
    
    def add_bookmark(self, title, url, folder='root'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bookmarks (title, url, folder) VALUES (?, ?, ?)', 
                      (title, url, folder))
        conn.commit()
        conn.close()
        print(f"[INFO] Bookmark added: {title}")
    
    def get_bookmarks(self, folder=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if folder:
            cursor.execute('SELECT id, title, url, folder FROM bookmarks WHERE folder = ?', (folder,))
        else:
            cursor.execute('SELECT id, title, url, folder FROM bookmarks')
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_folders(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT folder FROM bookmarks')
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results if results else ['root']
    
    def delete_bookmark(self, bookmark_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
        conn.commit()
        conn.close()
    
    def export_html(self, filepath):
        """HTML形式でエクスポート（Netscape Bookmark File Format）"""
        bookmarks = self.get_bookmarks()
        folders = {}
        
        for bm_id, title, url, folder in bookmarks:
            if folder not in folders:
                folders[folder] = []
            folders[folder].append((title, url))
        
        html = [
            '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
            '<!-- This is an automatically generated file.',
            '     It will be read and overwritten.',
            '     DO NOT EDIT! -->',
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            f'<TITLE>Bookmarks - {BROWSER_FULL_NAME}</TITLE>',
            '<H1>Bookmarks</H1>',
            '<DL><p>'
        ]
        
        for folder, items in folders.items():
            if folder != 'root':
                html.append(f'    <DT><H3>{escape(folder)}</H3>')
                html.append('    <DL><p>')
            
            for title, url in items:
                html.append(f'        <DT><A HREF="{escape(url)}">{escape(title)}</A>')
            
            if folder != 'root':
                html.append('    </DL><p>')
        
        html.append('</DL><p>')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))
        
        print(f"[INFO] Bookmarks exported to {filepath}")
    
    def import_html(self, filepath):
        """HTML形式でインポート"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            current_folder = 'root'
            h3_pattern = re.compile(r'<H3[^>]*>(.*?)</H3>', re.IGNORECASE)
            a_pattern = re.compile(r'<A\s+HREF="([^"]+)"[^>]*>(.*?)</A>', re.IGNORECASE)
            
            lines = content.split('\n')
            for line in lines:
                h3_match = h3_pattern.search(line)
                if h3_match:
                    current_folder = unescape(h3_match.group(1))
                    continue
                
                a_match = a_pattern.search(line)
                if a_match:
                    url = unescape(a_match.group(1))
                    title = unescape(a_match.group(2))
                    self.add_bookmark(title, url, current_folder)
            
            print(f"[INFO] Bookmarks imported from {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to import bookmarks: {e}")
            return False


class DownloadManager:
    """ダウンロード管理クラス"""
    
    def __init__(self):
        self.downloads = []
    
    def add_download(self, download_item):
        self.downloads.append(download_item)
        print(f"[INFO] Download started: {download_item.downloadFileName()}")
    
    def get_downloads(self):
        return self.downloads


class SessionManager:
    """セッション管理クラス"""
    
    def __init__(self):
        self.session_file = SESSION_FILE
    
    def save_session(self, tabs_data):
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(tabs_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Session saved: {len(tabs_data)} tabs")
        except Exception as e:
            print(f"[ERROR] Failed to save session: {e}")
    
    def load_session(self):
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    tabs_data = json.load(f)
                print(f"[INFO] Session loaded: {len(tabs_data)} tabs")
                return tabs_data
        except Exception as e:
            print(f"[ERROR] Failed to load session: {e}")
        return []


# =====================================================================
# スレッド
# =====================================================================

class UpdateChecker(QThread):
    """更新チェックを行うスレッド"""
    update_available = Signal(str, str)
    
    def run(self):
        print("[INFO] UpdateCheck Start")
        try:
            with urlopen(UPDATE_CHECK_URL, timeout=5) as response:
                content = response.read().decode('utf-8').strip()
                self.parse_update_info(content)
                print("[INFO] UpdateCheck Close")
        except (URLError, Exception) as e:
            print(f"[INFO] UpdateCheck Failed({e})")
    
    def parse_update_info(self, content):
        try:
            parts = content.split(',', 2)
            if len(parts) == 3 and parts[0] == "[VELA2]":
                latest_version = parts[1].strip()
                update_message = parts[2].strip()
                
                if version.parse(latest_version) > version.parse(BROWSER_VERSION_SEMANTIC):
                    print("[INFO] UpdateCheck-> New Version Available")
                    self.update_available.emit(latest_version, update_message)
                else:
                    print("[INFO] UpdateCheck-> Latest")
        except Exception as e:
            print(f"[INFO] UpdateCheck Failed({e})")


# =====================================================================
# ダイアログ群
# =====================================================================

class AddBookmarkDialog(QDialog):
    """ブックマーク追加ダイアログ（改善版）"""
    
    def __init__(self, title="", url="", folders=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ブックマークに追加")
        self.setMinimumWidth(500)
        self.result_data = None
        self.init_ui(title, url, folders or ['root'])
    
    def init_ui(self, title, url, folders):
        self.setStyleSheet(STYLES['dialog'])
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # タイトル
        title_label = QLabel("<h3>新しいブックマークを追加</h3>")
        layout.addWidget(title_label)
        
        # フォームレイアウト
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.title_input = QLineEdit(title)
        self.title_input.setPlaceholderText("ブックマークのタイトルを入力")
        form_layout.addRow("タイトル:", self.title_input)
        
        self.url_input = QLineEdit(url)
        self.url_input.setPlaceholderText("URLを入力")
        self.url_input.setReadOnly(True)
        form_layout.addRow("URL:", self.url_input)
        
        self.folder_combo = QComboBox()
        self.folder_combo.addItems(folders)
        form_layout.addRow("フォルダ:", self.folder_combo)
        
        layout.addLayout(form_layout)
        
        # 新しいフォルダ作成
        new_folder_layout = QHBoxLayout()
        self.new_folder_input = QLineEdit()
        self.new_folder_input.setPlaceholderText("新しいフォルダ名を入力（オプション）")
        new_folder_layout.addWidget(self.new_folder_input)
        
        add_folder_btn = QPushButton("フォルダを作成")
        add_folder_btn.setStyleSheet(STYLES['button_secondary'])
        add_folder_btn.clicked.connect(self.add_new_folder)
        new_folder_layout.addWidget(add_folder_btn)
        
        layout.addLayout(new_folder_layout)
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setStyleSheet(STYLES['button_secondary'])
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setMinimumWidth(100)
        save_btn.setStyleSheet(STYLES['button_primary'])
        save_btn.clicked.connect(self.save_bookmark)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def add_new_folder(self):
        folder_name = self.new_folder_input.text().strip()
        if folder_name and folder_name not in [self.folder_combo.itemText(i) for i in range(self.folder_combo.count())]:
            self.folder_combo.addItem(folder_name)
            self.folder_combo.setCurrentText(folder_name)
            self.new_folder_input.clear()
    
    def save_bookmark(self):
        title = self.title_input.text().strip()
        url = self.url_input.text().strip()
        folder = self.folder_combo.currentText()
        
        if title and url:
            self.result_data = {"title": title, "url": url, "folder": folder}
            self.accept()
        else:
            QMessageBox.warning(self, "入力エラー", "タイトルとURLを入力してください。")
    
    def get_result(self):
        return self.result_data


class MainDialog(QDialog):
    """メインダイアログ（ブラウザについて・設定・履歴・ブックマーク統合）"""
    
    open_url = Signal(str)
    
    def __init__(self, history_manager, bookmark_manager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.bookmark_manager = bookmark_manager
        self.setWindowTitle(f"{BROWSER_NAME}について")
        self.setMinimumSize(600, 500)
        self.settings = QSettings("VELABrowser", "Praxis_v1")
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet(STYLES['dialog'])
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # タブウィジェット
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(STYLES['tab_widget'])
        
        tab_widget.addTab(self.create_about_tab(), "ブラウザについて")
        tab_widget.addTab(self.create_settings_tab(), "設定")
        tab_widget.addTab(self.create_history_tab(), "閲覧履歴")
        tab_widget.addTab(self.create_bookmarks_tab(), "ブックマーク")
        
        layout.addWidget(tab_widget)
        
        # 閉じるボタン
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.addStretch()
        
        close_button = QPushButton("閉じる")
        close_button.setMinimumWidth(100)
        close_button.setStyleSheet(STYLES['button_primary'])
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def create_about_tab(self):
        """ブラウザについてタブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title_label = QLabel(f"<h1>{BROWSER_NAME} {BROWSER_CODENAME}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        version_label = QLabel(f"<h3>バージョン: {BROWSER_VERSION_NAME}</h3>")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        description = QLabel(
            f"<p style='font-size: 11pt;'>{BROWSER_NAME}は、左側に縦タブを配置した<br>"
            "シンプルで使いやすいWebブラウザです。</p>"
        )
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        tech_info = QTextEdit()
        tech_info.setReadOnly(True)
        tech_info.setMaximumHeight(120)
        
        from PySide6 import __version__ as pyside_version
        from PySide6.QtCore import qVersion
        
        tech_text = f"""• フレームワーク: PySide6 {pyside_version}
• Qt バージョン: {qVersion()}
• Python バージョン: {sys.version.split()[0]}
• エンジン: QtWebEngine (Chromium ベース)
• アーキテクチャ: {BROWSER_TARGET_Architecture}
• データディレクトリ: {DATA_DIR}"""
        tech_info.setPlainText(tech_text)
        layout.addWidget(tech_info)
        
        copyright_label = QLabel(
            "<p style='color: #666; font-size: 9pt;'>"
            "© 2025-2026, ABATBeliever.<br>"
            "Under LGPL v3 License"
            "</p>"
        )
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
        
        layout.addStretch()
        return widget
    
    def create_settings_tab(self):
        """設定タブ（スクロール対応）"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 一般設定
        general_group = QGroupBox("一般設定")
        general_layout = QVBoxLayout()
        
        homepage_layout = QHBoxLayout()
        homepage_layout.addWidget(QLabel("ホームページ:"))
        self.homepage_input = QLineEdit()
        self.homepage_input.setText(self.settings.value("homepage", "https://www.google.com"))
        homepage_layout.addWidget(self.homepage_input)
        general_layout.addLayout(homepage_layout)
        
        startup_layout = QHBoxLayout()
        startup_layout.addWidget(QLabel("起動時:"))
        self.startup_combo = QComboBox()
        self.startup_combo.addItems(["前回のセッションを復元", "ホームページを開く", "新しいタブを開く"])
        self.startup_combo.setCurrentIndex(self.settings.value("startup_action", 0, type=int))
        startup_layout.addWidget(self.startup_combo)
        general_layout.addLayout(startup_layout)
        
        self.save_session_check = QCheckBox("終了時にセッションを保存")
        self.save_session_check.setChecked(self.settings.value("save_session", True, type=bool))
        general_layout.addWidget(self.save_session_check)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # 検索設定
        search_group = QGroupBox("検索設定")
        search_layout = QVBoxLayout()
        
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("検索エンジン:"))
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.addItems(["Google", "Bing", "DuckDuckGo", "Yahoo! JAPAN"])
        self.search_engine_combo.setCurrentIndex(self.settings.value("search_engine", 0, type=int))
        engine_layout.addWidget(self.search_engine_combo)
        search_layout.addLayout(engine_layout)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # プライバシー設定
        privacy_group = QGroupBox("プライバシー設定")
        privacy_layout = QVBoxLayout()
        
        self.do_not_track_check = QCheckBox("Do Not Track を送信")
        self.do_not_track_check.setChecked(self.settings.value("do_not_track", False, type=bool))
        privacy_layout.addWidget(self.do_not_track_check)
        
        self.clear_on_exit_check = QCheckBox("終了時に履歴を削除")
        self.clear_on_exit_check.setChecked(self.settings.value("clear_on_exit", False, type=bool))
        privacy_layout.addWidget(self.clear_on_exit_check)
        
        privacy_group.setLayout(privacy_layout)
        layout.addWidget(privacy_group)
        
        # ダウンロード設定
        download_group = QGroupBox("ダウンロード設定")
        download_layout = QVBoxLayout()
        
        download_dir_layout = QHBoxLayout()
        download_dir_layout.addWidget(QLabel("保存先:"))
        self.download_dir_input = QLineEdit()
        self.download_dir_input.setText(self.settings.value("download_dir", str(DOWNLOADS_DIR)))
        download_dir_layout.addWidget(self.download_dir_input)
        
        browse_btn = QPushButton("参照")
        browse_btn.clicked.connect(self.browse_download_dir)
        download_dir_layout.addWidget(browse_btn)
        download_layout.addLayout(download_dir_layout)
        
        self.ask_download_check = QCheckBox("ダウンロード時に保存場所を確認")
        self.ask_download_check.setChecked(self.settings.value("ask_download", True, type=bool))
        download_layout.addWidget(self.ask_download_check)
        
        download_group.setLayout(download_layout)
        layout.addWidget(download_group)
        
        # 外観設定
        appearance_group = QGroupBox("外観設定")
        appearance_layout = QVBoxLayout()
        
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("デフォルトズーム:"))
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(50, 200)
        self.zoom_spin.setValue(self.settings.value("default_zoom", 100, type=int))
        self.zoom_spin.setSuffix("%")
        zoom_layout.addWidget(self.zoom_spin)
        zoom_layout.addStretch()
        appearance_layout.addLayout(zoom_layout)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # 詳細設定
        advanced_group = QGroupBox("詳細設定")
        advanced_layout = QVBoxLayout()
        
        self.javascript_check = QCheckBox("JavaScript を有効にする")
        self.javascript_check.setChecked(self.settings.value("enable_javascript", True, type=bool))
        advanced_layout.addWidget(self.javascript_check)
        
        self.plugins_check = QCheckBox("プラグインを有効にする")
        self.plugins_check.setChecked(self.settings.value("enable_plugins", True, type=bool))
        advanced_layout.addWidget(self.plugins_check)
        
        self.fullscreen_check = QCheckBox("全画面表示を許可")
        self.fullscreen_check.setChecked(self.settings.value("allow_fullscreen", True, type=bool))
        advanced_layout.addWidget(self.fullscreen_check)
        
        self.images_check = QCheckBox("画像を自動的に読み込む")
        self.images_check.setChecked(self.settings.value("auto_load_images", True, type=bool))
        advanced_layout.addWidget(self.images_check)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # UserAgent設定
        useragent_group = QGroupBox("UserAgent設定")
        useragent_layout = QVBoxLayout()
        
        ua_preset_layout = QHBoxLayout()
        ua_preset_layout.addWidget(QLabel("プリセット:"))
        self.ua_preset_combo = QComboBox()
        self.ua_preset_combo.addItems([
            "デフォルト (Chrome/Windows)",
            "Firefox/Windows",
            "Safari/macOS",
            "Chrome/Android",
            "Safari/iOS",
            "カスタム"
        ])
        self.ua_preset_combo.setCurrentIndex(self.settings.value("ua_preset", 0, type=int))
        self.ua_preset_combo.currentIndexChanged.connect(self.on_ua_preset_changed)
        ua_preset_layout.addWidget(self.ua_preset_combo)
        useragent_layout.addLayout(ua_preset_layout)
        
        self.ua_custom_input = QLineEdit()
        self.ua_custom_input.setPlaceholderText("カスタムUserAgentを入力")
        self.ua_custom_input.setText(self.settings.value("ua_custom", ""))
        useragent_layout.addWidget(self.ua_custom_input)
        
        useragent_group.setLayout(useragent_layout)
        layout.addWidget(useragent_group)
        
        # 保存ボタン
        save_btn = QPushButton("設定を保存")
        save_btn.setStyleSheet(STYLES['button_primary'])
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        scroll_area.setWidget(widget)
        return scroll_area
    
    def create_history_tab(self):
        """閲覧履歴タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 検索バー
        search_layout = QHBoxLayout()
        self.history_search_input = QLineEdit()
        self.history_search_input.setPlaceholderText("履歴を検索...")
        self.history_search_input.textChanged.connect(self.search_history)
        search_layout.addWidget(self.history_search_input)
        
        clear_history_btn = QPushButton("履歴を全削除")
        clear_history_btn.setStyleSheet(STYLES['button_secondary'])
        clear_history_btn.clicked.connect(self.clear_history)
        search_layout.addWidget(clear_history_btn)
        
        layout.addLayout(search_layout)
        
        # 履歴テーブル
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["タイトル", "URL", "訪問日時", "訪問回数"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.doubleClicked.connect(self.on_history_item_double_clicked)
        layout.addWidget(self.history_table)
        
        self.load_history()
        
        return widget
    
    def create_bookmarks_tab(self):
        """ブックマークタブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # ツールバー
        toolbar_layout = QHBoxLayout()
        
        delete_btn = QPushButton("削除")
        delete_btn.setStyleSheet(STYLES['button_secondary'])
        delete_btn.clicked.connect(self.delete_selected_bookmark)
        toolbar_layout.addWidget(delete_btn)
        
        toolbar_layout.addStretch()
        
        export_btn = QPushButton("エクスポート")
        export_btn.setStyleSheet(STYLES['button_secondary'])
        export_btn.clicked.connect(self.export_bookmarks)
        toolbar_layout.addWidget(export_btn)
        
        import_btn = QPushButton("インポート")
        import_btn.setStyleSheet(STYLES['button_secondary'])
        import_btn.clicked.connect(self.import_bookmarks)
        toolbar_layout.addWidget(import_btn)
        
        layout.addLayout(toolbar_layout)
        
        # ブックマークツリー
        self.bookmark_tree = QTreeWidget()
        self.bookmark_tree.setHeaderLabels(["タイトル", "URL"])
        self.bookmark_tree.setColumnWidth(0, 300)
        self.bookmark_tree.itemDoubleClicked.connect(self.on_bookmark_item_double_clicked)
        layout.addWidget(self.bookmark_tree)
        
        self.load_bookmarks()
        
        return widget
    
    def browse_download_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "ダウンロードフォルダを選択",
            self.download_dir_input.text()
        )
        if directory:
            self.download_dir_input.setText(directory)
    
    def on_ua_preset_changed(self, index):
        presets = {
            0: "",
            1: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            2: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            3: "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.135 Mobile Safari/537.36",
            4: "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            5: self.ua_custom_input.text()
        }
        
        if index < 5:
            self.ua_custom_input.setEnabled(False)
            self.ua_custom_input.setPlaceholderText(presets.get(index, ""))
        else:
            self.ua_custom_input.setEnabled(True)
    
    def save_settings(self):
        self.settings.setValue("homepage", self.homepage_input.text())
        self.settings.setValue("startup_action", self.startup_combo.currentIndex())
        self.settings.setValue("save_session", self.save_session_check.isChecked())
        self.settings.setValue("search_engine", self.search_engine_combo.currentIndex())
        self.settings.setValue("do_not_track", self.do_not_track_check.isChecked())
        self.settings.setValue("clear_on_exit", self.clear_on_exit_check.isChecked())
        self.settings.setValue("download_dir", self.download_dir_input.text())
        self.settings.setValue("ask_download", self.ask_download_check.isChecked())
        self.settings.setValue("default_zoom", self.zoom_spin.value())
        self.settings.setValue("enable_javascript", self.javascript_check.isChecked())
        self.settings.setValue("enable_plugins", self.plugins_check.isChecked())
        self.settings.setValue("allow_fullscreen", self.fullscreen_check.isChecked())
        self.settings.setValue("auto_load_images", self.images_check.isChecked())
        self.settings.setValue("ua_preset", self.ua_preset_combo.currentIndex())
        self.settings.setValue("ua_custom", self.ua_custom_input.text())
        
        self.settings.sync()
        
        QMessageBox.information(self, "保存完了", "設定を保存しました。\n一部の設定は再起動後に反映されます。")
    
    def load_history(self):
        history = self.history_manager.get_history(500)
        self.display_history(history)
    
    def search_history(self, query):
        if query:
            history = self.history_manager.search_history(query)
        else:
            history = self.history_manager.get_history(500)
        self.display_history(history)
    
    def display_history(self, history):
        self.history_table.setRowCount(len(history))
        for i, (url, title, visit_time, visit_count) in enumerate(history):
            self.history_table.setItem(i, 0, QTableWidgetItem(title or ""))
            self.history_table.setItem(i, 1, QTableWidgetItem(url))
            self.history_table.setItem(i, 2, QTableWidgetItem(visit_time))
            self.history_table.setItem(i, 3, QTableWidgetItem(str(visit_count)))
    
    def on_history_item_double_clicked(self, index):
        row = index.row()
        url = self.history_table.item(row, 1).text()
        self.open_url.emit(url)
        self.close()
    
    def clear_history(self):
        reply = QMessageBox.question(
            self, "確認", "本当に全ての履歴を削除しますか？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self.load_history()
    
    def load_bookmarks(self):
        self.bookmark_tree.clear()
        folders = {}
        
        bookmarks = self.bookmark_manager.get_bookmarks()
        
        for bm_id, title, url, folder in bookmarks:
            if folder not in folders:
                folder_item = QTreeWidgetItem(self.bookmark_tree, [folder, ""])
                folder_item.setData(0, Qt.UserRole, {"type": "folder", "name": folder})
                folders[folder] = folder_item
            
            bookmark_item = QTreeWidgetItem(folders[folder], [title, url])
            bookmark_item.setData(0, Qt.UserRole, {"type": "bookmark", "id": bm_id, "url": url})
        
        self.bookmark_tree.expandAll()
    
    def delete_selected_bookmark(self):
        current_item = self.bookmark_tree.currentItem()
        if current_item:
            data = current_item.data(0, Qt.UserRole)
            if data and data["type"] == "bookmark":
                reply = QMessageBox.question(
                    self, "確認", "このブックマークを削除しますか？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.bookmark_manager.delete_bookmark(data["id"])
                    self.load_bookmarks()
    
    def on_bookmark_item_double_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data and data["type"] == "bookmark":
            self.open_url.emit(data["url"])
            self.close()
    
    def export_bookmarks(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "ブックマークをエクスポート", 
            str(DATA_DIR / "bookmarks.html"),
            "HTML Files (*.html)"
        )
        if filepath:
            self.bookmark_manager.export_html(filepath)
            QMessageBox.information(self, "完了", "ブックマークをエクスポートしました。")
    
    def import_bookmarks(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "ブックマークをインポート",
            str(Path.home()),
            "HTML Files (*.html)"
        )
        if filepath:
            if self.bookmark_manager.import_html(filepath):
                self.load_bookmarks()
                QMessageBox.information(self, "完了", "ブックマークをインポートしました。")
            else:
                QMessageBox.warning(self, "エラー", "ブックマークのインポートに失敗しました。")


class DownloadDialog(QDialog):
    """ダウンロードマネージャーダイアログ"""
    
    def __init__(self, download_manager, parent=None):
        super().__init__(parent)
        self.download_manager = download_manager
        self.setWindowTitle("ダウンロードマネージャー")
        self.setMinimumSize(700, 400)
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet(STYLES['dialog'])
        layout = QVBoxLayout(self)
        
        self.download_table = QTableWidget()
        self.download_table.setColumnCount(4)
        self.download_table.setHorizontalHeaderLabels(["ファイル名", "URL", "進捗", "状態"])
        self.download_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.download_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.download_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.download_table)
        
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("更新")
        refresh_btn.setStyleSheet(STYLES['button_secondary'])
        refresh_btn.clicked.connect(self.refresh_downloads)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("閉じる")
        close_btn.setStyleSheet(STYLES['button_primary'])
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.refresh_downloads()
    
    def refresh_downloads(self):
        downloads = self.download_manager.get_downloads()
        self.download_table.setRowCount(len(downloads))
        
        for i, download in enumerate(downloads):
            self.download_table.setItem(i, 0, QTableWidgetItem(download.downloadFileName()))
            self.download_table.setItem(i, 1, QTableWidgetItem(download.url().toString()))
            
            progress = QProgressBar()
            progress.setValue(int(download.receivedBytes() / max(download.totalBytes(), 1) * 100))
            self.download_table.setCellWidget(i, 2, progress)
            
            state_map = {
                QWebEngineDownloadRequest.DownloadRequested: "要求中",
                QWebEngineDownloadRequest.DownloadInProgress: "ダウンロード中",
                QWebEngineDownloadRequest.DownloadCompleted: "完了",
                QWebEngineDownloadRequest.DownloadCancelled: "キャンセル",
                QWebEngineDownloadRequest.DownloadInterrupted: "中断"
            }
            state = state_map.get(download.state(), "不明")
            self.download_table.setItem(i, 3, QTableWidgetItem(state))


# =====================================================================
# WebEngine関連
# =====================================================================

class CustomWebEnginePage(QWebEnginePage):
    """カスタムWebEnginePage"""
    
    new_tab_requested = Signal(QUrl)
    
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
    
    def createWindow(self, window_type):
        print("[INFO] TabControl: Add")
        page = CustomWebEnginePage(self.profile(), self.parent())
        page.new_tab_requested.connect(self.new_tab_requested.emit)
        page.urlChanged.connect(lambda url: self.new_tab_requested.emit(url))
        return page


class TabItem(QListWidgetItem):
    """タブアイテム"""
    def __init__(self, title, web_view):
        super().__init__(title)
        self.web_view = web_view
        self.url = web_view.url()


# =====================================================================
# メインブラウザウィンドウ
# =====================================================================

class VerticalTabBrowser(QMainWindow):
    """縦タブブラウザのメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.tabs = []
        self.profile = QWebEngineProfile.defaultProfile()
        self.history_manager = HistoryManager()
        self.bookmark_manager = BookmarkManager()
        self.download_manager = DownloadManager()
        self.session_manager = SessionManager()
        self.settings = QSettings("VELABrowser", "Praxis_v1")
        
        self.apply_settings()
        self.init_ui()
        self.check_for_updates()
        self.restore_session()
    
    def apply_settings(self):
        """設定を適用"""
        web_settings = self.profile.settings()
        
        web_settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, 
                                 self.settings.value("allow_fullscreen", True, type=bool))
        web_settings.setAttribute(QWebEngineSettings.JavascriptEnabled, 
                                 self.settings.value("enable_javascript", True, type=bool))
        web_settings.setAttribute(QWebEngineSettings.PluginsEnabled, 
                                 self.settings.value("enable_plugins", True, type=bool))
        web_settings.setAttribute(QWebEngineSettings.AutoLoadImages,
                                 self.settings.value("auto_load_images", True, type=bool))
        
        # UserAgent設定
        ua_preset = self.settings.value("ua_preset", 0, type=int)
        if ua_preset > 0:
            ua_strings = {
                1: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
                2: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
                3: "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.135 Mobile Safari/537.36",
                4: "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
                5: self.settings.value("ua_custom", "")
            }
            ua = ua_strings.get(ua_preset, "")
            if ua:
                self.profile.setHttpUserAgent(ua)
                print(f"[INFO] UserAgent set to preset {ua_preset}")
        
        self.profile.downloadRequested.connect(self.on_download_requested)
        print("[INFO] Settings applied")
    
    def on_download_requested(self, download):
        print(f"[INFO] Download requested: {download.downloadFileName()}")
        
        download_dir = Path(self.settings.value("download_dir", str(DOWNLOADS_DIR)))
        download_dir.mkdir(parents=True, exist_ok=True)
        
        if self.settings.value("ask_download", True, type=bool):
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "ファイルを保存",
                str(download_dir / download.downloadFileName()),
                "All Files (*)"
            )
            if filepath:
                download.setDownloadDirectory(str(Path(filepath).parent))
                download.setDownloadFileName(Path(filepath).name)
                download.accept()
                self.download_manager.add_download(download)
        else:
            download.setDownloadDirectory(str(download_dir))
            download.accept()
            self.download_manager.add_download(download)
    
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle(f"{BROWSER_FULL_NAME}")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(STYLES['main_window'])
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(STYLES['splitter'])
        
        self.tab_list_widget = self.create_tab_list()
        splitter.addWidget(self.tab_list_widget)
        
        browser_widget = self.create_browser_area()
        splitter.addWidget(browser_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([200, 1000])
        
        main_layout.addWidget(splitter)
    
    def restore_session(self):
        startup_action = self.settings.value("startup_action", 0, type=int)
        
        if startup_action == 0 and self.settings.value("save_session", True, type=bool):
            tabs_data = self.session_manager.load_session()
            if tabs_data:
                for i, tab_data in enumerate(tabs_data):
                    self.add_new_tab(tab_data.get("url", "https://www.google.com"), 
                                   activate=(i == tab_data.get("active_index", 0)))
                return
        
        if startup_action == 1:
            homepage = self.settings.value("homepage", "https://www.google.com")
            self.add_new_tab(homepage)
        else:
            self.add_new_tab("https://www.google.com")
    
    def save_current_session(self):
        if not self.settings.value("save_session", True, type=bool):
            return
        
        tabs_data = []
        current_index = self.tab_list.currentRow()
        
        for i in range(self.tab_list.count()):
            item = self.tab_list.item(i)
            if isinstance(item, TabItem):
                tabs_data.append({
                    "url": item.web_view.url().toString(),
                    "title": item.text(),
                    "active_index": current_index
                })
        
        self.session_manager.save_session(tabs_data)
    
    def check_for_updates(self):
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self.show_update_notification)
        self.update_checker.start()
    
    def show_update_notification(self, latest_version, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("更新が利用可能です")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"<h3>VELAの新しいバージョン({latest_version}) が利用可能です</h3>")
        msg_box.setInformativeText(
            f"<p>現在のバージョン: {BROWSER_VERSION_SEMANTIC}<br>最新のバージョン: {latest_version}</p>"
            f"<p><b>更新内容:</b></p><p>{message}</p>"
        )
        msg_box.exec()
    
    def show_main_dialog(self):
        """メインダイアログ表示"""
        old_settings = {
            "javascript": self.settings.value("enable_javascript", True, type=bool),
            "plugins": self.settings.value("enable_plugins", True, type=bool),
            "images": self.settings.value("auto_load_images", True, type=bool),
            "ua_preset": self.settings.value("ua_preset", 0, type=int)
        }
        
        dialog = MainDialog(self.history_manager, self.bookmark_manager, self)
        dialog.open_url.connect(lambda url: self.add_new_tab(url, activate=True))
        dialog.exec()
        
        new_settings = {
            "javascript": self.settings.value("enable_javascript", True, type=bool),
            "plugins": self.settings.value("enable_plugins", True, type=bool),
            "images": self.settings.value("auto_load_images", True, type=bool),
            "ua_preset": self.settings.value("ua_preset", 0, type=int)
        }
        
        if old_settings != new_settings:
            self.apply_settings()
    
    def show_download_dialog(self):
        dialog = DownloadDialog(self.download_manager, self)
        dialog.exec()
    
    def add_bookmark_from_current_tab(self):
        """現在のタブをブックマークに追加"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            url = current_item.web_view.url().toString()
            title = current_item.web_view.title() or "無題"
            
            folders = self.bookmark_manager.get_folders()
            dialog = AddBookmarkDialog(title, url, folders, self)
            
            if dialog.exec() == QDialog.Accepted:
                result = dialog.get_result()
                if result:
                    self.bookmark_manager.add_bookmark(
                        result["title"], 
                        result["url"], 
                        result["folder"]
                    )
    
    def create_tab_list(self):
        widget = QWidget()
        widget.setStyleSheet(STYLES['tab_list'])
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        new_tab_btn = QPushButton()
        new_tab_btn.setIcon(qta.icon('fa5s.plus', color='#0078d4'))
        new_tab_btn.setToolTip("新規タブ")
        new_tab_btn.setFixedSize(36, 36)
        new_tab_btn.clicked.connect(lambda: self.add_new_tab(self.settings.value("homepage", "https://www.google.com")))
        button_layout.addWidget(new_tab_btn)
        
        close_tab_btn = QPushButton()
        close_tab_btn.setIcon(qta.icon('fa5s.times', color='#d13438'))
        close_tab_btn.setToolTip("タブを閉じる")
        close_tab_btn.setFixedSize(36, 36)
        close_tab_btn.clicked.connect(self.close_current_tab)
        button_layout.addWidget(close_tab_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.tab_list = QListWidget()
        self.tab_list.currentItemChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_list)
        
        return widget
    
    def create_browser_area(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet(STYLES['toolbar'])
        layout.addWidget(toolbar)
        
        self.back_btn = QPushButton()
        self.back_btn.setIcon(qta.icon('fa5s.arrow-left', color='#333'))
        self.back_btn.setToolTip("戻る")
        self.back_btn.setFixedSize(32, 32)
        self.back_btn.clicked.connect(self.go_back)
        toolbar.addWidget(self.back_btn)
        
        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(qta.icon('fa5s.arrow-right', color='#333'))
        self.forward_btn.setToolTip("進む")
        self.forward_btn.setFixedSize(32, 32)
        self.forward_btn.clicked.connect(self.go_forward)
        toolbar.addWidget(self.forward_btn)
        
        self.reload_btn = QPushButton()
        self.reload_btn.setIcon(qta.icon('fa5s.sync-alt', color='#333'))
        self.reload_btn.setToolTip("再読み込み")
        self.reload_btn.setFixedSize(32, 32)
        self.reload_btn.clicked.connect(self.reload_page)
        toolbar.addWidget(self.reload_btn)
        
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("URLを入力またはキーワードで検索")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.url_bar)
        
        go_btn = QPushButton()
        go_btn.setIcon(qta.icon('fa5s.search', color='#0078d4'))
        go_btn.setToolTip("移動/検索")
        go_btn.setFixedSize(32, 32)
        go_btn.clicked.connect(self.navigate_to_url)
        toolbar.addWidget(go_btn)
        
        bookmark_add_btn = QPushButton()
        bookmark_add_btn.setIcon(qta.icon('fa5s.star', color='#f4c430'))
        bookmark_add_btn.setToolTip("ブックマークに追加")
        bookmark_add_btn.setFixedSize(32, 32)
        bookmark_add_btn.clicked.connect(self.add_bookmark_from_current_tab)
        toolbar.addWidget(bookmark_add_btn)
        
        download_btn = QPushButton()
        download_btn.setIcon(qta.icon('fa5s.download', color='#666'))
        download_btn.setToolTip("ダウンロード")
        download_btn.setFixedSize(32, 32)
        download_btn.clicked.connect(self.show_download_dialog)
        toolbar.addWidget(download_btn)
        
        settings_btn = QPushButton()
        settings_btn.setIcon(qta.icon('fa5s.cog', color='#666'))
        settings_btn.setToolTip("設定・履歴・ブックマーク")
        settings_btn.setFixedSize(32, 32)
        settings_btn.clicked.connect(self.show_main_dialog)
        toolbar.addWidget(settings_btn)
        
        self.web_container = QWidget()
        self.web_layout = QVBoxLayout(self.web_container)
        self.web_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_container)
        
        return widget
    
    def get_search_url(self, query):
        search_engine = self.settings.value("search_engine", 0, type=int)
        encoded_query = quote_plus(query)
        
        search_urls = {
            0: f"https://www.google.com/search?q={encoded_query}",
            1: f"https://www.bing.com/search?q={encoded_query}",
            2: f"https://duckduckgo.com/?q={encoded_query}",
            3: f"https://search.yahoo.co.jp/search?p={encoded_query}"
        }
        
        return search_urls.get(search_engine, search_urls[0])
    
    def is_valid_url(self, text):
        url_pattern = re.compile(r'^https?://|^www\.|^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}')
        
        if ' ' in text:
            return False
        
        if url_pattern.match(text):
            return True
        
        if '.' in text and not text.startswith('.') and not text.endswith('.'):
            parts = text.split('.')
            if len(parts) >= 2 and len(parts[-1]) >= 2:
                return True
        
        return False
    
    def process_url_or_search(self, text):
        text = text.strip()
        
        if self.is_valid_url(text):
            if not text.startswith("http://") and not text.startswith("https://"):
                text = "https://" + text
            return text
        else:
            return self.get_search_url(text)
    
    def add_new_tab(self, url, activate=True):
        web_view = QWebEngineView()
        
        default_zoom = self.settings.value("default_zoom", 100, type=int)
        web_view.setZoomFactor(default_zoom / 100.0)
        
        page = CustomWebEnginePage(self.profile, web_view)
        page.new_tab_requested.connect(lambda url: self.add_new_tab(url.toString(), activate=True))
        page.fullScreenRequested.connect(self.handle_fullscreen_request)
        
        web_view.setPage(page)
        web_view.setUrl(QUrl(url))
        
        web_view.titleChanged.connect(lambda title: self.update_tab_title(web_view, title))
        web_view.urlChanged.connect(lambda url: self.update_url_bar(web_view, url))
        web_view.loadFinished.connect(lambda: self.on_load_finished(web_view))
        
        tab_item = TabItem("新しいタブ", web_view)
        
        self.tab_list.addItem(tab_item)
        self.tabs.append(web_view)
        
        if activate:
            self.tab_list.setCurrentItem(tab_item)
    
    def handle_fullscreen_request(self, request):
        if request.toggleOn():
            print("[INFO] Fullscreen: ON")
            request.accept()
        else:
            print("[INFO] Fullscreen: OFF")
            request.accept()
    
    def on_load_finished(self, web_view):
        url = web_view.url().toString()
        title = web_view.title()
        self.history_manager.add_history(url, title)
    
    def on_tab_changed(self, current, previous):
        if current is None:
            return
        
        for i in reversed(range(self.web_layout.count())):
            widget = self.web_layout.itemAt(i).widget()
            if widget:
                self.web_layout.removeWidget(widget)
                widget.setParent(None)
        
        tab_item = current
        web_view = tab_item.web_view
        self.web_layout.addWidget(web_view)
        web_view.show()
        
        self.url_bar.setText(web_view.url().toString())
    
    def update_tab_title(self, web_view, title):
        for i in range(self.tab_list.count()):
            item = self.tab_list.item(i)
            if isinstance(item, TabItem) and item.web_view == web_view:
                display_title = title[:30] + "..." if len(title) > 30 else title
                item.setText(display_title)
                break
    
    def update_url_bar(self, web_view, url):
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            if current_item.web_view == web_view:
                self.url_bar.setText(url.toString())
    
    def navigate_to_url(self):
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            text = self.url_bar.text()
            url = self.process_url_or_search(text)
            current_item.web_view.setUrl(QUrl(url))
    
    def go_back(self):
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            current_item.web_view.back()
    
    def go_forward(self):
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            current_item.web_view.forward()
    
    def reload_page(self):
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            current_item.web_view.reload()
    
    def close_current_tab(self):
        current_row = self.tab_list.currentRow()
        if current_row >= 0 and self.tab_list.count() > 1:
            item = self.tab_list.takeItem(current_row)
            if isinstance(item, TabItem):
                item.web_view.deleteLater()
                self.tabs.remove(item.web_view)
                print("[INFO] TabControl: Close")
        elif self.tab_list.count() == 1:
            print("[INFO] TabControl: Close(Exit)")
            self.close()
    
    def closeEvent(self, event):
        self.save_current_session()
        
        if self.settings.value("clear_on_exit", False, type=bool):
            self.history_manager.clear_history()
        
        event.accept()


# =====================================================================
# メイン
# =====================================================================

def main():
    app = QApplication(sys.argv)
    
    font = QFont()
    font.setPointSize(9)
    app.setFont(font)
    
    browser = VerticalTabBrowser()
    browser.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
