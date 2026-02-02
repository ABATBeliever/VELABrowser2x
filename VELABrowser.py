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

from PySide6.QtCore import Qt, QUrl, Signal, QThread, QSettings
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLineEdit, QListWidget,
    QListWidgetItem, QSplitter, QToolBar, QDialog,
    QTabWidget, QLabel, QTextEdit, QFrame, QMessageBox,
    QCheckBox, QSpinBox, QComboBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtGui import QIcon, QAction, QFont
import qtawesome as qta

# ブラウザ情報
BROWSER_NAME                = "VELA"
BROWSER_CODENAME            = "Praxis"
BROWSER_VERSION_SEMANTIC    = "2.0.0.0a5"  # セマンティックバージョン（比較用）
BROWSER_VERSION_NAME        = "2.0.0.0 Alpha5" # バージョン名
BROWSER_FULL_NAME           = f"{BROWSER_NAME} {BROWSER_CODENAME} {BROWSER_VERSION_NAME}"
BROWSER_TARGET_Architecture = "win-x64" # linux-x64-debian / linux-x64-redhat / rasp-a64 / win-a64 / win-x64

# 更新チェックURL
UPDATE_CHECK_URL = f"https://abatbeliever.net/upd/VELABrowser/{BROWSER_CODENAME}/{BROWSER_TARGET_Architecture}.updat"

# データディレクトリ
DATA_DIR = Path.home() / ".vela_browser"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_DB = DATA_DIR / "history.db"
SESSION_FILE = DATA_DIR / "session.json"

print(BROWSER_FULL_NAME)
print("\nCopyright (C) 2025-2026 ABATBeliever")


class HistoryManager:
    """履歴管理クラス"""
    
    def __init__(self):
        self.db_path = HISTORY_DB
        self.init_database()
    
    def init_database(self):
        """データベースの初期化"""
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
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url ON history(url)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_visit_time ON history(visit_time DESC)
        ''')
        conn.commit()
        conn.close()
        print("[INFO] History database initialized")
    
    def add_history(self, url, title):
        """履歴を追加"""
        if not url or url.startswith("about:") or url.startswith("chrome:"):
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 既存のエントリをチェック
        cursor.execute('SELECT id, visit_count FROM history WHERE url = ?', (url,))
        result = cursor.fetchone()
        
        if result:
            # 既存エントリを更新
            cursor.execute('''
                UPDATE history 
                SET title = ?, visit_time = CURRENT_TIMESTAMP, visit_count = ?
                WHERE id = ?
            ''', (title, result[1] + 1, result[0]))
        else:
            # 新規エントリを追加
            cursor.execute('''
                INSERT INTO history (url, title) VALUES (?, ?)
            ''', (url, title))
        
        conn.commit()
        conn.close()
    
    def get_history(self, limit=100):
        """履歴を取得"""
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
        """履歴を検索"""
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
        """履歴を全削除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM history')
        conn.commit()
        conn.close()
        print("[INFO] History cleared")


class SessionManager:
    """セッション管理クラス"""
    
    def __init__(self):
        self.session_file = SESSION_FILE
    
    def save_session(self, tabs_data):
        """セッションを保存"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(tabs_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Session saved: {len(tabs_data)} tabs")
        except Exception as e:
            print(f"[ERROR] Failed to save session: {e}")
    
    def load_session(self):
        """セッションを読み込み"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    tabs_data = json.load(f)
                print(f"[INFO] Session loaded: {len(tabs_data)} tabs")
                return tabs_data
        except Exception as e:
            print(f"[ERROR] Failed to load session: {e}")
        return []


class UpdateChecker(QThread):
    """更新チェックを行うスレッド"""
    update_available = Signal(str, str)
    
    def run(self):
        """更新チェックを実行"""
        print("[INFO] UpdateCheck Start")
        try:
            with urlopen(UPDATE_CHECK_URL, timeout=5) as response:
                content = response.read().decode('utf-8').strip()
                self.parse_update_info(content)
                print("[INFO] UpdateCheck Close")
        except (URLError, Exception) as e:
            print(f"[INFO] UpdateCheck Failed({e})")
    
    def parse_update_info(self, content):
        """更新情報をパース"""
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


class HistoryDialog(QDialog):
    """履歴表示ダイアログ"""
    
    open_url = Signal(str)
    
    def __init__(self, history_manager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.setWindowTitle("閲覧履歴")
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.load_history()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        
        # 検索バー
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("履歴を検索...")
        self.search_input.textChanged.connect(self.search_history)
        search_layout.addWidget(self.search_input)
        
        clear_btn = QPushButton("履歴を全削除")
        clear_btn.clicked.connect(self.clear_history)
        search_layout.addWidget(clear_btn)
        
        layout.addLayout(search_layout)
        
        # 履歴テーブル
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["タイトル", "URL", "訪問日時", "訪問回数"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.doubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.history_table)
        
        # 閉じるボタン
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def load_history(self):
        """履歴を読み込んで表示"""
        history = self.history_manager.get_history(500)
        self.display_history(history)
    
    def search_history(self, query):
        """履歴を検索"""
        if query:
            history = self.history_manager.search_history(query)
        else:
            history = self.history_manager.get_history(500)
        self.display_history(history)
    
    def display_history(self, history):
        """履歴をテーブルに表示"""
        self.history_table.setRowCount(len(history))
        for i, (url, title, visit_time, visit_count) in enumerate(history):
            self.history_table.setItem(i, 0, QTableWidgetItem(title or ""))
            self.history_table.setItem(i, 1, QTableWidgetItem(url))
            self.history_table.setItem(i, 2, QTableWidgetItem(visit_time))
            self.history_table.setItem(i, 3, QTableWidgetItem(str(visit_count)))
    
    def on_item_double_clicked(self, index):
        """アイテムダブルクリック時"""
        row = index.row()
        url = self.history_table.item(row, 1).text()
        self.open_url.emit(url)
        self.close()
    
    def clear_history(self):
        """履歴を全削除"""
        reply = QMessageBox.question(
            self, "確認", "本当に全ての履歴を削除しますか？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self.load_history()


class AboutDialog(QDialog):
    """ブラウザについて/設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{BROWSER_NAME}について")
        self.setMinimumSize(700, 600)
        self.settings = QSettings("ABATBeliever", "VELA")
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #0078d4;
            }
        """)
        
        tab_widget.addTab(self.create_about_tab(), "ブラウザについて")
        tab_widget.addTab(self.create_settings_tab(), "設定")
        
        layout.addWidget(tab_widget)
        
        # 閉じるボタン
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.addStretch()
        
        close_button = QPushButton("閉じる")
        close_button.setMinimumWidth(100)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
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
• データディレクトリ: {DATA_DIR}
"""
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
        """設定タブ（UI仮組み）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # 一般設定グループ
        general_group = QGroupBox("一般設定")
        general_layout = QVBoxLayout()
        
        # ホームページ設定
        homepage_layout = QHBoxLayout()
        homepage_layout.addWidget(QLabel("ホームページ:"))
        self.homepage_input = QLineEdit()
        self.homepage_input.setText(self.settings.value("homepage", "https://www.google.com"))
        homepage_layout.addWidget(self.homepage_input)
        general_layout.addLayout(homepage_layout)
        
        # 起動時の動作
        startup_layout = QHBoxLayout()
        startup_layout.addWidget(QLabel("起動時:"))
        self.startup_combo = QComboBox()
        self.startup_combo.addItems(["前回のセッションを復元", "ホームページを開く", "新しいタブを開く"])
        self.startup_combo.setCurrentIndex(self.settings.value("startup_action", 0, type=int))
        startup_layout.addWidget(self.startup_combo)
        general_layout.addLayout(startup_layout)
        
        # セッション保存
        self.save_session_check = QCheckBox("終了時にセッションを保存")
        self.save_session_check.setChecked(self.settings.value("save_session", True, type=bool))
        general_layout.addWidget(self.save_session_check)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # 検索設定グループ
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
        
        # プライバシー設定グループ
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
        
        # 外観設定グループ
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
        
        # 詳細設定グループ
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
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # 保存ボタン
        save_btn = QPushButton("設定を保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        return widget
    
    def save_settings(self):
        """設定を保存"""
        self.settings.setValue("homepage", self.homepage_input.text())
        self.settings.setValue("startup_action", self.startup_combo.currentIndex())
        self.settings.setValue("save_session", self.save_session_check.isChecked())
        self.settings.setValue("search_engine", self.search_engine_combo.currentIndex())
        self.settings.setValue("do_not_track", self.do_not_track_check.isChecked())
        self.settings.setValue("clear_on_exit", self.clear_on_exit_check.isChecked())
        self.settings.setValue("default_zoom", self.zoom_spin.value())
        self.settings.setValue("enable_javascript", self.javascript_check.isChecked())
        self.settings.setValue("enable_plugins", self.plugins_check.isChecked())
        self.settings.setValue("allow_fullscreen", self.fullscreen_check.isChecked())
        
        QMessageBox.information(self, "保存完了", "設定を保存しました。\n一部の設定は再起動後に反映されます。")


class CustomWebEnginePage(QWebEnginePage):
    """カスタムWebEnginePage"""
    
    new_tab_requested = Signal(QUrl)
    
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        
    def createWindow(self, window_type):
        """新しいウィンドウ/タブが要求された時の処理"""
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


class VerticalTabBrowser(QMainWindow):
    """縦タブブラウザのメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.tabs = []
        self.profile = QWebEngineProfile.defaultProfile()
        self.history_manager = HistoryManager()
        self.session_manager = SessionManager()
        self.settings = QSettings("ABATBeliever", "VELA")
        
        # WebEngineの設定
        web_settings = self.profile.settings()
        web_settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        
        self.init_ui()
        self.check_for_updates()
        self.restore_session()
        
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle(f"{BROWSER_FULL_NAME}")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QToolBar {
                background-color: #f5f5f5;
                border-bottom: 1px solid #e0e0e0;
                spacing: 5px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
                width: 1px;
            }
        """)
        
        self.tab_list_widget = self.create_tab_list()
        splitter.addWidget(self.tab_list_widget)
        
        browser_widget = self.create_browser_area()
        splitter.addWidget(browser_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([200, 1000])
        
        main_layout.addWidget(splitter)
    
    def restore_session(self):
        """セッションを復元"""
        if self.settings.value("save_session", True, type=bool):
            tabs_data = self.session_manager.load_session()
            if tabs_data:
                for i, tab_data in enumerate(tabs_data):
                    self.add_new_tab(tab_data.get("url", "https://www.google.com"), activate=(i == tab_data.get("active_index", 0)))
                return
        
        # セッションがない場合はデフォルトタブを開く
        homepage = self.settings.value("homepage", "https://www.google.com")
        self.add_new_tab(homepage)
    
    def save_current_session(self):
        """現在のセッションを保存"""
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
        """更新チェック"""
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self.show_update_notification)
        self.update_checker.start()
    
    def show_update_notification(self, latest_version, message):
        """更新通知"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("更新が利用可能です")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"<h3>VELAの新しいバージョン({latest_version}) が利用可能です</h3>")
        msg_box.setInformativeText(
            f"<p>現在のバージョン: {BROWSER_VERSION_SEMANTIC}<br>最新のバージョン: {latest_version}</p>"
            f"<p><b>更新内容:</b></p><p>{message}</p>"
        )
        msg_box.exec()
    
    def show_about_dialog(self):
        """設定ダイアログ表示"""
        dialog = AboutDialog(self)
        dialog.exec()
    
    def show_history_dialog(self):
        """履歴ダイアログ表示"""
        dialog = HistoryDialog(self.history_manager, self)
        dialog.open_url.connect(lambda url: self.add_new_tab(url, activate=True))
        dialog.exec()
    
    def create_tab_list(self):
        """タブリスト作成"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f9f9f9;
                border-right: 1px solid #e0e0e0;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        new_tab_btn = QPushButton()
        new_tab_btn.setIcon(qta.icon('fa5s.plus', color='#0078d4'))
        new_tab_btn.setToolTip("新規タブ")
        new_tab_btn.setFixedSize(36, 36)
        new_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e6f2ff;
                border-color: #0078d4;
            }
        """)
        new_tab_btn.clicked.connect(lambda: self.add_new_tab(self.settings.value("homepage", "https://www.google.com")))
        button_layout.addWidget(new_tab_btn)
        
        close_tab_btn = QPushButton()
        close_tab_btn.setIcon(qta.icon('fa5s.times', color='#d13438'))
        close_tab_btn.setToolTip("タブを閉じる")
        close_tab_btn.setFixedSize(36, 36)
        close_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ffe6e6;
                border-color: #d13438;
            }
        """)
        close_tab_btn.clicked.connect(self.close_current_tab)
        button_layout.addWidget(close_tab_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.tab_list = QListWidget()
        self.tab_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e6f2ff;
                color: #0078d4;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.tab_list.currentItemChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_list)
        
        return widget
    
    def create_browser_area(self):
        """ブラウザエリア作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f5f5f5;
                border-bottom: 1px solid #e0e0e0;
                spacing: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #e6f2ff;
                border-color: #0078d4;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
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
        
        # 履歴ボタン追加
        history_btn = QPushButton()
        history_btn.setIcon(qta.icon('fa5s.history', color='#666'))
        history_btn.setToolTip("履歴")
        history_btn.setFixedSize(32, 32)
        history_btn.clicked.connect(self.show_history_dialog)
        toolbar.addWidget(history_btn)
        
        settings_btn = QPushButton()
        settings_btn.setIcon(qta.icon('fa5s.cog', color='#666'))
        settings_btn.setToolTip("設定")
        settings_btn.setFixedSize(32, 32)
        settings_btn.clicked.connect(self.show_about_dialog)
        toolbar.addWidget(settings_btn)
        
        self.web_container = QWidget()
        self.web_layout = QVBoxLayout(self.web_container)
        self.web_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_container)
        
        return widget
    
    def is_valid_url(self, text):
        """URL判定"""
        print("[INFO] TextCheck Start")
        url_pattern = re.compile(r'^https?://|^www\.|^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}')
        
        if ' ' in text:
            print("[INFO] TextCheck: Text")
            return False
        
        if url_pattern.match(text):
            print("[INFO] TextCheck: URL")
            return True
        
        if '.' in text and not text.startswith('.') and not text.endswith('.'):
            parts = text.split('.')
            if len(parts) >= 2 and len(parts[-1]) >= 2:
                print("[INFO] TextCheck: URL")
                return True
        
        print("[INFO] TextCheck: Text")
        return False
    
    def process_url_or_search(self, text):
        """URL/検索処理"""
        text = text.strip()
        
        if self.is_valid_url(text):
            if not text.startswith("http://") and not text.startswith("https://"):
                text = "https://" + text
            return text
        else:
            search_query = quote_plus(text)
            return f"https://www.google.com/search?q={search_query}"
    
    def add_new_tab(self, url, activate=True):
        """新規タブ追加"""
        web_view = QWebEngineView()
        
        page = CustomWebEnginePage(self.profile, web_view)
        page.new_tab_requested.connect(lambda url: self.add_new_tab(url.toString(), activate=True))
        
        # 全画面表示のサポート
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
        """全画面表示リクエスト処理"""
        if request.toggleOn():
            print("[INFO] Fullscreen: ON")
            request.accept()
            # 全画面表示時の処理
        else:
            print("[INFO] Fullscreen: OFF")
            request.accept()
    
    def on_load_finished(self, web_view):
        """ページ読み込み完了時"""
        url = web_view.url().toString()
        title = web_view.title()
        self.history_manager.add_history(url, title)
    
    def on_tab_changed(self, current, previous):
        """タブ切り替え"""
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
        """タブタイトル更新"""
        for i in range(self.tab_list.count()):
            item = self.tab_list.item(i)
            if isinstance(item, TabItem) and item.web_view == web_view:
                display_title = title[:30] + "..." if len(title) > 30 else title
                item.setText(display_title)
                break
    
    def update_url_bar(self, web_view, url):
        """URLバー更新"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            if current_item.web_view == web_view:
                self.url_bar.setText(url.toString())
    
    def navigate_to_url(self):
        """URL移動"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            text = self.url_bar.text()
            url = self.process_url_or_search(text)
            current_item.web_view.setUrl(QUrl(url))
    
    def go_back(self):
        """戻る"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            current_item.web_view.back()
    
    def go_forward(self):
        """進む"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            current_item.web_view.forward()
    
    def reload_page(self):
        """再読み込み"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            current_item.web_view.reload()
    
    def close_current_tab(self):
        """タブを閉じる"""
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
        """終了時の処理"""
        self.save_current_session()
        
        # 終了時に履歴を削除する設定の場合
        if self.settings.value("clear_on_exit", False, type=bool):
            self.history_manager.clear_history()
        
        event.accept()


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
