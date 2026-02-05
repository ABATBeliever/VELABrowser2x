"""
VELA Browser - メインブラウザウィンドウ
縦タブブラウザの実装、カスタムWebEnginePage、タブアイテム
"""

import re
from pathlib import Path
from urllib.parse import quote_plus

from PySide6.QtCore import Qt, QUrl, QSettings
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QListWidget, QSplitter, QToolBar, QMessageBox,
    QFileDialog, QApplication, QMenu
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtGui import QFont, QAction
import qtawesome as qta

from constants import STYLES, BROWSER_FULL_NAME, BROWSER_VERSION_SEMANTIC, DOWNLOADS_DIR, USER_AGENT_PRESETS
from managers import HistoryManager, BookmarkManager, DownloadManager, SessionManager, UpdateChecker
from dialogs import AddBookmarkDialog, MainDialog, FindDialog


from PySide6.QtCore import QUrl, Signal
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWidgets import QListWidgetItem


# =====================================================================
# カスタムWebEnginePage
# =====================================================================

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


# =====================================================================
# タブアイテム
# =====================================================================

class TabItem(QListWidgetItem):
    """タブを表すリストアイテム"""
    
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
        self.settings = QSettings("ABATBeliever", "VELA")
        
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
            if ua_preset == 5:
                ua = self.settings.value("ua_custom", "")
            else:
                ua = USER_AGENT_PRESETS.get(ua_preset, "")
            
            if ua:
                self.profile.setHttpUserAgent(ua)
                print(f"[INFO] UserAgent set to preset {ua_preset}")
        
        self.profile.downloadRequested.connect(self.on_download_requested)
        print("[INFO] Settings applied")
    
    def on_download_requested(self, download):
        """ダウンロード要求時の処理"""
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
                # ダウンロード開始時にダウンロードマネージャーを表示
                self.show_download_dialog()
        else:
            download.setDownloadDirectory(str(download_dir))
            download.accept()
            self.download_manager.add_download(download)
            # ダウンロード開始時にダウンロードマネージャーを表示
            self.show_download_dialog()
    
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
        """セッションを復元"""
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
    
    def show_menu(self):
        """メニューを表示"""
        menu = QMenu(self)
        menu.setStyleSheet(STYLES['menu'])
        
        # 新しいタブ
        new_tab_action = QAction(qta.icon('fa5s.plus', color='#4a90d9'), "新しいタブ", self)
        new_tab_action.triggered.connect(lambda: self.add_new_tab("https://www.google.com", activate=True))
        menu.addAction(new_tab_action)
        
        menu.addSeparator()
        
        # ブックマーク
        bookmark_action = QAction(qta.icon('fa5s.star', color='#f4c430'), "ブックマーク", self)
        bookmark_action.triggered.connect(self.show_bookmarks_dialog)
        menu.addAction(bookmark_action)
        
        # 履歴
        history_action = QAction(qta.icon('fa5s.history', color='#666'), "履歴", self)
        history_action.triggered.connect(self.show_history_dialog)
        menu.addAction(history_action)
        
        # ダウンロード
        download_action = QAction(qta.icon('fa5s.download', color='#666'), "ダウンロード", self)
        download_action.triggered.connect(self.show_download_dialog)
        menu.addAction(download_action)
        
        menu.addSeparator()
        
        # ローカルファイルを開く
        local_action = QAction(qta.icon('fa5s.folder-open', color='#666'), "ローカルファイルを開く", self)
        local_action.triggered.connect(self.open_local_file)
        menu.addAction(local_action)
        
        # ページ内を検索
        find_action = QAction(qta.icon('fa5s.search', color='#666'), "ページ内を検索", self)
        find_action.triggered.connect(self.find_in_page)
        menu.addAction(find_action)
        
        menu.addSeparator()
        
        # 設定
        settings_action = QAction(qta.icon('fa5s.cog', color='#666'), "設定", self)
        settings_action.triggered.connect(self.show_main_dialog)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # 終了
        exit_action = QAction(qta.icon('fa5s.sign-out-alt', color='#d9534f'), "終了", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
        
        # メニューを表示（ボタンの下に）
        sender = self.sender()
        if sender:
            menu.exec(sender.mapToGlobal(sender.rect().bottomLeft()))
    
    def show_bookmarks_dialog(self):
        """ブックマークダイアログを表示"""
        dialog = MainDialog(self.history_manager, self.bookmark_manager, self.download_manager, self)
        dialog.open_url.connect(lambda url: self.add_new_tab(url, activate=True))
        dialog.tab_widget.setCurrentIndex(3)  # ブックマークタブを選択
        dialog.exec()
    
    def show_history_dialog(self):
        """履歴ダイアログを表示"""
        dialog = MainDialog(self.history_manager, self.bookmark_manager, self.download_manager, self)
        dialog.open_url.connect(lambda url: self.add_new_tab(url, activate=True))
        dialog.tab_widget.setCurrentIndex(2)  # 履歴タブを選択
        dialog.exec()
    
    def open_local_file(self):
        """ローカルファイルを新しいタブで開く"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "ローカルファイルを開く",
            str(Path.home()),
            "All Files (*)"
        )
        if filepath:
            file_url = QUrl.fromLocalFile(filepath)
            self.add_new_tab(file_url.toString(), activate=True)
    
    def find_in_page(self):
        """ページ内検索（改良版ダイアログ）"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            dialog = FindDialog(current_item.web_view, self)
            dialog.exec()
    
    def show_main_dialog(self):
        """メインダイアログ表示"""
        old_settings = {
            "javascript": self.settings.value("enable_javascript", True, type=bool),
            "plugins": self.settings.value("enable_plugins", True, type=bool),
            "images": self.settings.value("auto_load_images", True, type=bool),
            "fullscreen": self.settings.value("allow_fullscreen", True, type=bool),
            "ua_preset": self.settings.value("ua_preset", 0, type=int),
            "ua_custom": self.settings.value("ua_custom", "")
        }
        
        dialog = MainDialog(self.history_manager, self.bookmark_manager, self.download_manager, self)
        dialog.open_url.connect(lambda url: self.add_new_tab(url, activate=True))
        dialog.exec()
        
        new_settings = {
            "javascript": self.settings.value("enable_javascript", True, type=bool),
            "plugins": self.settings.value("enable_plugins", True, type=bool),
            "images": self.settings.value("auto_load_images", True, type=bool),
            "fullscreen": self.settings.value("allow_fullscreen", True, type=bool),
            "ua_preset": self.settings.value("ua_preset", 0, type=int),
            "ua_custom": self.settings.value("ua_custom", "")
        }
        
        # 設定変更があれば再起動を提案
        if old_settings != new_settings:
            reply = QMessageBox.question(
                self,
                "再起動の確認",
                "設定を完全に反映するにはブラウザの再起動が必要です。\n今すぐ再起動しますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.save_current_session()
                QApplication.quit()
            else:
                # 一部の設定のみ即座に適用を試みる
                self.apply_settings()
    
    def show_download_dialog(self):
        """ダウンロードマネージャー表示"""
        dialog = MainDialog(self.history_manager, self.bookmark_manager, self.download_manager, self)
        dialog.open_url.connect(lambda url: self.add_new_tab(url, activate=True))
        dialog.show_download_tab()  # ダウンロードタブを表示
        dialog.exec()
    
    def add_bookmark_from_current_tab(self):
        """現在のタブをブックマークに追加"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            url = current_item.web_view.url().toString()
            title = current_item.web_view.title() or "無題"
            
            folders = self.bookmark_manager.get_folders()
            dialog = AddBookmarkDialog(title, url, folders, self)
            
            if dialog.exec():
                result = dialog.get_result()
                if result:
                    self.bookmark_manager.add_bookmark(
                        result["title"], 
                        result["url"], 
                        result["folder"]
                    )
    
    def create_tab_list(self):
        """タブリスト作成"""
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
        """ブラウザエリア作成"""
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
        
        bookmark_add_btn = QPushButton()
        bookmark_add_btn.setIcon(qta.icon('fa5s.star', color='#f4c430'))
        bookmark_add_btn.setToolTip("ブックマークに追加")
        bookmark_add_btn.setFixedSize(32, 32)
        bookmark_add_btn.clicked.connect(self.add_bookmark_from_current_tab)
        toolbar.addWidget(bookmark_add_btn)
        
        menu_btn = QPushButton()
        menu_btn.setIcon(qta.icon('fa5s.ellipsis-h', color='#666'))
        menu_btn.setToolTip("メニュー")
        menu_btn.setFixedSize(32, 32)
        menu_btn.clicked.connect(self.show_menu)
        toolbar.addWidget(menu_btn)
        
        self.web_container = QWidget()
        self.web_layout = QVBoxLayout(self.web_container)
        self.web_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_container)
        
        return widget
    
    def get_search_url(self, query):
        """検索エンジンに応じた検索URLを取得"""
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
        """URL判定"""
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
        """URL/検索処理"""
        text = text.strip()
        
        if self.is_valid_url(text):
            if not text.startswith("http://") and not text.startswith("https://"):
                text = "https://" + text
            return text
        else:
            return self.get_search_url(text)
    
    def add_new_tab(self, url, activate=True):
        """新規タブ追加"""
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
        """全画面表示リクエスト処理"""
        if request.toggleOn():
            print("[INFO] Fullscreen: ON")
            request.accept()
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
        
        if self.settings.value("clear_on_exit", False, type=bool):
            self.history_manager.clear_history()
        
        event.accept()
