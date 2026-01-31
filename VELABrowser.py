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
from urllib.parse import quote_plus
from urllib.request import urlopen
from urllib.error import URLError
from packaging import version

from PySide6.QtCore import Qt, QUrl, Signal, QThread
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLineEdit, QListWidget,
    QListWidgetItem, QSplitter, QToolBar, QDialog,
    QTabWidget, QLabel, QTextEdit, QFrame, QMessageBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtGui import QIcon, QAction, QFont
import qtawesome as qta

# ブラウザ情報
BROWSER_NAME                = "VELA"
BROWSER_CODENAME            = "Praxis"
BROWSER_VERSION_SEMANTIC    = "2.0.0.0a4"  # セマンティックバージョン（比較用）
BROWSER_VERSION_NAME        = "2.0.0.0 Alpha4" # バージョン名
BROWSER_FULL_NAME           = f"{BROWSER_NAME} {BROWSER_CODENAME} {BROWSER_VERSION_NAME}"
BROWSER_TARGET_Architecture = "win-x64"
                                 #linux-x64-debian / linux-x64-redhat / rasp-a64 / win-a64 / win-x64

# 更新チェックURL
UPDATE_CHECK_URL = f"https://abatbeliever.net/upd/VELABrowser/{BROWSER_CODENAME}/{BROWSER_TARGET_Architecture}.updat"

print(BROWSER_FULL_NAME)
print("\nCopyright (C) 2025-2026 ABATBeliever")

class UpdateChecker(QThread):
    """更新チェックを行うスレッド"""
    update_available = Signal(str, str)  # version, message
    print("[INFO] UpdateCheck Start")
    
    def run(self):
        """更新チェックを実行"""
        try:
            with urlopen(UPDATE_CHECK_URL, timeout=5) as response:
                content = response.read().decode('utf-8').strip()
                self.parse_update_info(content)
                print("[INFO] UpdateCheck Close")
        except (URLError, Exception) as e:
            # エラーは無視（更新チェック失敗時は何もしない）
            print(f"[INFO] UpdateCheck Failed({e})")
    
    def parse_update_info(self, content):
        """更新情報をパース"""
        try:
            parts = content.split(',', 2)
            if len(parts) == 3 and parts[0] == "[VELA2]":
                latest_version = parts[1].strip()
                update_message = parts[2].strip()
                
                # バージョン比較
                if version.parse(latest_version) > version.parse(BROWSER_VERSION_SEMANTIC):
                    print("[INFO] UpdateCheck-> New Version Avaliable")
                    self.update_available.emit(latest_version, update_message)
                else:
                    print("[INFO] UpdateCheck-> Latest")
        except Exception as e:
            print(f"[INFO] UpdateCheck Failed({e})")

class AboutDialog(QDialog):
    """ブラウザについて/設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{BROWSER_NAME}について")
        self.setMinimumSize(600, 500)
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # タブウィジェット
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
        
        # 「ブラウザについて」タブ
        about_tab = self.create_about_tab()
        tab_widget.addTab(about_tab, "ブラウザについて")
        
        # 「設定」タブ
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "設定")
        
        layout.addWidget(tab_widget)
        
        # ボタンエリア
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
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def create_about_tab(self):
        """ブラウザについてタブの作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        
        # ブラウザ名
        title_label = QLabel(f"<h1>{BROWSER_NAME} {BROWSER_CODENAME}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # バージョン情報
        version_label = QLabel(f"<h3>バージョン: {BROWSER_VERSION_NAME}</h3>")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(line)
        
        # 説明文
        description = QLabel(
            f"<p style='font-size: 11pt;'>{BROWSER_NAME}は、左側に縦タブを配置した<br>"
            "シンプルで使いやすいWebブラウザです。</p>"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # 技術情報
        tech_info = QTextEdit()
        tech_info.setReadOnly(True)
        tech_info.setMaximumHeight(120)
        tech_info.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 2px;
                font-family: 'Courier New', monospace;
            }
        """)
        
        from PySide6 import __version__ as pyside_version
        from PySide6.QtCore import qVersion
        
        tech_text = f"""• フレームワーク: PySide6 {pyside_version}
• Qt バージョン: {qVersion()}
• Python バージョン: {sys.version.split()[0]}
• エンジン: QtWebEngine (Chromium ベース)
• アーキテクチャ: {BROWSER_TARGET_Architecture}
"""
        tech_info.setPlainText(tech_text)
        layout.addWidget(tech_info)
        
        # 著作権情報
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
        """設定タブの作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # タイトル
        title_label = QLabel("<h2>設定</h2>")
        layout.addWidget(title_label)
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(line)
        
        # プレースホルダー
        placeholder_label = QLabel(
            "<p style='font-size: 11pt;'>設定機能は今後のバージョンで実装予定です。</p>"
            "<p style='font-size: 10pt; color: #666;'>実装予定の機能:</p>"
        )
        layout.addWidget(placeholder_label)
        
        # 機能リスト
        features_text = QTextEdit()
        features_text.setReadOnly(True)
        features_text.setMaximumHeight(200)
        features_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        features_text.setPlainText(
            "• デフォルトのホームページ設定\n"
            "• 検索エンジンの選択\n"
            "• 履歴\n"
            "• プライバシー設定\n"
            "• 広告ブロック\n"
            "• UserAgent変更"
        )
        layout.addWidget(features_text)
        
        layout.addStretch()
        
        return widget


class CustomWebEnginePage(QWebEnginePage):
    """新しいウィンドウ/タブの処理をカスタマイズしたWebEnginePage"""
    
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
    """タブを表すリストアイテム"""
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
        self.init_ui()
        self.check_for_updates()
        
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle(f"{BROWSER_FULL_NAME}")
        self.setGeometry(100, 100, 1200, 800)
        
        # スタイルシート適用
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
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # スプリッター
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
                width: 1px;
            }
        """)
        
        # 左側：タブリスト
        self.tab_list_widget = self.create_tab_list()
        splitter.addWidget(self.tab_list_widget)
        
        # 右側：ブラウザエリア
        browser_widget = self.create_browser_area()
        splitter.addWidget(browser_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([200, 1000])
        
        main_layout.addWidget(splitter)
        
        # 最初のタブを作成
        self.add_new_tab("https://www.google.com")
    
    def check_for_updates(self):
        """更新チェックを開始"""
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self.show_update_notification)
        self.update_checker.start()
    
    def show_update_notification(self, latest_version, message):
        """更新通知を表示"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("更新が利用可能です")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"<h3>VELAの新しいバージョン({latest_version}) が利用可能です</h3>")
        msg_box.setInformativeText(
            f"<p>現在のバージョン: {BROWSER_VERSION_SEMANTIC}<br>最新のバージョン: {latest_version}</p>"
            f"<p><b>更新内容:</b></p>"
            f"<p>{message}</p>"
        )
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: #333;
            }
        """)
        msg_box.exec()
    
    def show_about_dialog(self):
        """ブラウザについてダイアログを表示"""
        dialog = AboutDialog(self)
        dialog.exec()
        
    def create_tab_list(self):
        """左側のタブリストを作成"""
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
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        # 新規タブボタン
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
            QPushButton:pressed {
                background-color: #cce4ff;
            }
        """)
        new_tab_btn.clicked.connect(lambda: self.add_new_tab("https://www.google.com"))
        button_layout.addWidget(new_tab_btn)
        
        # タブを閉じるボタン
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
            QPushButton:pressed {
                background-color: #ffcccc;
            }
        """)
        close_tab_btn.clicked.connect(self.close_current_tab)
        button_layout.addWidget(close_tab_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # タブリスト
        self.tab_list = QListWidget()
        self.tab_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 2px;
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
        """右側のブラウザエリアを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ツールバー
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
            QPushButton:pressed {
                background-color: #cce4ff;
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
        
        # 戻るボタン
        self.back_btn = QPushButton()
        self.back_btn.setIcon(qta.icon('fa5s.arrow-left', color='#333'))
        self.back_btn.setToolTip("戻る")
        self.back_btn.setFixedSize(32, 32)
        self.back_btn.clicked.connect(self.go_back)
        toolbar.addWidget(self.back_btn)
        
        # 進むボタン
        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(qta.icon('fa5s.arrow-right', color='#333'))
        self.forward_btn.setToolTip("進む")
        self.forward_btn.setFixedSize(32, 32)
        self.forward_btn.clicked.connect(self.go_forward)
        toolbar.addWidget(self.forward_btn)
        
        # 更新ボタン
        self.reload_btn = QPushButton()
        self.reload_btn.setIcon(qta.icon('fa5s.sync-alt', color='#333'))
        self.reload_btn.setToolTip("再読み込み")
        self.reload_btn.setFixedSize(32, 32)
        self.reload_btn.clicked.connect(self.reload_page)
        toolbar.addWidget(self.reload_btn)
        
        # アドレスバー
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("URLを入力またはキーワードで検索")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.url_bar)
        
        # 検索/移動ボタン
        go_btn = QPushButton()
        go_btn.setIcon(qta.icon('fa5s.search', color='#0078d4'))
        go_btn.setToolTip("移動/検索")
        go_btn.setFixedSize(32, 32)
        go_btn.clicked.connect(self.navigate_to_url)
        toolbar.addWidget(go_btn)
        
        # 設定ボタン
        settings_btn = QPushButton()
        settings_btn.setIcon(qta.icon('fa5s.cog', color='#666'))
        settings_btn.setToolTip("設定")
        settings_btn.setFixedSize(32, 32)
        settings_btn.clicked.connect(self.show_about_dialog)
        toolbar.addWidget(settings_btn)
        
        # WebViewコンテナ
        self.web_container = QWidget()
        self.web_layout = QVBoxLayout(self.web_container)
        self.web_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_container)
        
        return widget
    
    def is_valid_url(self, text):
        """テキストが有効なURLかどうかを判定"""
        print("[INFO] TextCheck Start")
        url_pattern = re.compile(
            r'^https?://'
            r'|^www\.'
            r'|^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        )
        
        if ' ' in text:
            print("[INFO] TabControl: Text")
            return False
        
        if url_pattern.match(text):
            print("[INFO] TabControl: URL")
            return True
        
        if '.' in text and not text.startswith('.') and not text.endswith('.'):
            parts = text.split('.')
            if len(parts) >= 2 and len(parts[-1]) >= 2:
                print("[INFO] TabControl: URL")
                return True
        print("[INFO] TabControl: Text")
        return False
    
    def process_url_or_search(self, text):
        """URLまたは検索クエリを処理"""
        text = text.strip()
        
        if self.is_valid_url(text):
            if not text.startswith("http://") and not text.startswith("https://"):
                text = "https://" + text
            return text
        else:
            search_query = quote_plus(text)
            return f"https://www.google.com/search?q={search_query}"
    
    def add_new_tab(self, url, activate=True):
        """新しいタブを追加"""
        web_view = QWebEngineView()
        
        page = CustomWebEnginePage(self.profile, web_view)
        page.new_tab_requested.connect(lambda url: self.add_new_tab(url.toString(), activate=True))
        web_view.setPage(page)
        
        web_view.setUrl(QUrl(url))
        
        web_view.titleChanged.connect(lambda title: self.update_tab_title(web_view, title))
        web_view.urlChanged.connect(lambda url: self.update_url_bar(web_view, url))
        
        tab_item = TabItem("新しいタブ", web_view)
        
        self.tab_list.addItem(tab_item)
        self.tabs.append(web_view)
        
        if activate:
            self.tab_list.setCurrentItem(tab_item)
    
    def on_tab_changed(self, current, previous):
        """タブが切り替わった時の処理"""
        if current is None:
            return
        
        for i in reversed(range(self.web_layout.count())):
            widget = self.web_layout.itemAt(i).widget()
            if widget:
                self.web_layout.removeWidget(widget)
                widget.setParent(None)
                print("[INFO] TabControl: Elected{i}")
        
        tab_item = current
        web_view = tab_item.web_view
        self.web_layout.addWidget(web_view)
        web_view.show()
        
        self.url_bar.setText(web_view.url().toString())
    
    def update_tab_title(self, web_view, title):
        """タブのタイトルを更新"""
        for i in range(self.tab_list.count()):
            item = self.tab_list.item(i)
            if isinstance(item, TabItem) and item.web_view == web_view:
                display_title = title[:30] + "..." if len(title) > 30 else title
                item.setText(display_title)
                break
    
    def update_url_bar(self, web_view, url):
        """URLバーを更新"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            if current_item.web_view == web_view:
                self.url_bar.setText(url.toString())
    
    def navigate_to_url(self):
        """URLバーのアドレスに移動または検索"""
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
        """現在のタブを閉じる"""
        current_row = self.tab_list.currentRow()
        if current_row >= 0 and self.tab_list.count() > 1:
            item = self.tab_list.takeItem(current_row)
            if isinstance(item, TabItem):
                item.web_view.deleteLater()
                self.tabs.remove(item.web_view)
                print("[INFO] TabControl: Close")
        elif self.tab_list.count() == 1:
            print("[INFO] TabControl: Close(Exit)")
            sys.exit(0)


def main():
    app = QApplication(sys.argv)
    
    # アプリケーション全体のフォント設定
    font = QFont()
    font.setPointSize(9)
    app.setFont(font)
    
    browser = VerticalTabBrowser()
    browser.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
