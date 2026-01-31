# VELA 2.0.0.0a3
# LGPL v3

import sys
import re
from urllib.parse import quote_plus

# ブラウザ情報
BROWSER_NAME = "VELA"
BROWSER_VERSION = "2.0.0.0a3"
BROWSER_FULL_NAME = f"{BROWSER_NAME} {BROWSER_VERSION}"
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLineEdit, QListWidget,
    QListWidgetItem, QSplitter, QToolBar, QDialog,
    QTabWidget, QLabel, QTextEdit, QFrame
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtGui import QIcon, QAction
import qtawesome as qta


class AboutDialog(QDialog):
    """ブラウザについて/設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{BROWSER_NAME}について")
        self.setMinimumSize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        
        # タブウィジェット
        tab_widget = QTabWidget()
        
        # 「ブラウザについて」タブ
        about_tab = self.create_about_tab()
        tab_widget.addTab(about_tab, "ブラウザについて")
        
        # 「設定」タブ
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "設定")
        
        layout.addWidget(tab_widget)
        
        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
    
    def create_about_tab(self):
        """ブラウザについてタブの作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # ブラウザ名とバージョン
        title_label = QLabel(f"<h1>{BROWSER_NAME}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        version_label = QLabel(f"<h3>バージョン {BROWSER_VERSION}</h3>")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 説明文
        description = QLabel(
            f"<p>{BROWSER_NAME}は、左側に縦タブを配置した<br>"
            "シンプルで使いやすいWebブラウザです。</p>"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # 技術情報
        tech_info = QTextEdit()
        tech_info.setReadOnly(True)
        tech_info.setMaximumHeight(150)
        
        from PySide6 import __version__ as pyside_version
        from PySide6.QtCore import qVersion
        
        tech_text = f"""技術情報:
• フレームワーク: PySide6 {pyside_version}
• Qt バージョン: {qVersion()}
• Python バージョン: {sys.version.split()[0]}
• エンジン: QtWebEngine (Chromium ベース)
"""
        tech_info.setPlainText(tech_text)
        layout.addWidget(tech_info)
        
        # 著作権情報
        copyright_label = QLabel(
            "<p style='color: gray; font-size: 10pt;'>"
            "© 2025-2026 ABATBeliever<br>"
            "Built with PySide6 and QtWebEngine"
            "</p>"
        )
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
        
        layout.addStretch()
        
        return widget
    
    def create_settings_tab(self):
        """設定タブの作成（今後の拡張用）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # プレースホルダー
        placeholder_label = QLabel(
            "<h3>設定</h3>"
            "<p>設定機能は今後のバージョンで実装予定です。</p>"
            "<p>実装予定の機能:</p>"
            "<ul>"
            "<li>デフォルトのホームページ</li>"
            "<li>検索エンジンの選択</li>"
            "<li>タブの表示設定</li>"
            "<li>プライバシー設定</li>"
            "<li>外観のカスタマイズ</li>"
            "</ul>"
        )
        placeholder_label.setWordWrap(True)
        layout.addWidget(placeholder_label)
        
        layout.addStretch()
        
        return widget


class CustomWebEnginePage(QWebEnginePage):
    """新しいウィンドウ/タブの処理をカスタマイズしたWebEnginePage"""
    
    new_tab_requested = Signal(QUrl)
    
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
    
    def createWindow(self, window_type):
        """新しいウィンドウ/タブが要求された時の処理"""
        # 新しいページを作成して返す
        page = CustomWebEnginePage(self.profile(), self.parent())
        page.new_tab_requested.connect(self.new_tab_requested.emit)
        
        # URLが設定されたらシグナルを発火
        page.urlChanged.connect(lambda url: self.new_tab_requested.emit(url))
        
        return page


class TabItem(QListWidgetItem):
    """タブを表すリストアイテム"""
    def __init__(self, title, web_view):
        super().__init__(title)
        self.web_view = web_view
        self.url = web_view.url()


class VerticalTabBrowser(QMainWindow):
    """縦タブブラウザのメインウィンドウ Alpha2"""
    
    def __init__(self):
        super().__init__()
        self.tabs = []  # WebViewのリスト
        self.profile = QWebEngineProfile.defaultProfile()
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle(f"{BROWSER_FULL_NAME}")
        self.setGeometry(100, 100, 1200, 800)
        
        # メニューバーの作成
        self.create_menu_bar()
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト（横方向）
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # スプリッターで左右を分割
        splitter = QSplitter(Qt.Horizontal)
        
        # 左側：タブリスト
        self.tab_list_widget = self.create_tab_list()
        splitter.addWidget(self.tab_list_widget)
        
        # 右側：ブラウザエリア
        browser_widget = self.create_browser_area()
        splitter.addWidget(browser_widget)
        
        # スプリッターの初期サイズ設定（左:右 = 1:4）
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([200, 1000])
        
        main_layout.addWidget(splitter)
        
        # 最初のタブを作成
        self.add_new_tab("https://www.google.com")
    
    def create_menu_bar(self):
        """メニューバーの作成"""
        menubar = self.menuBar()
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)(仮)")
        
        # 「ブラウザについて」アクション
        about_action = QAction(f"{BROWSER_NAME}について(&A)", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def show_about_dialog(self):
        """ブラウザについてダイアログを表示"""
        dialog = AboutDialog(self)
        dialog.exec()
        
    def create_tab_list(self):
        """左側のタブリストを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # ボタンエリア（横並び）
        button_layout = QHBoxLayout()
        
        # 新規タブボタン（アイコン）
        new_tab_btn = QPushButton()
        new_tab_btn.setIcon(qta.icon('fa5s.plus', color='green'))
        new_tab_btn.setToolTip("新規タブ")
        new_tab_btn.setFixedSize(40, 40)
        new_tab_btn.clicked.connect(lambda: self.add_new_tab("https://www.google.com"))
        button_layout.addWidget(new_tab_btn)
        
        # タブを閉じるボタン（アイコン）
        close_tab_btn = QPushButton()
        close_tab_btn.setIcon(qta.icon('fa5s.times', color='red'))
        close_tab_btn.setToolTip("タブを閉じる")
        close_tab_btn.setFixedSize(40, 40)
        close_tab_btn.clicked.connect(self.close_current_tab)
        button_layout.addWidget(close_tab_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # タブリスト
        self.tab_list = QListWidget()
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
        layout.addWidget(toolbar)
        
        # 戻るボタン
        self.back_btn = QPushButton()
        self.back_btn.setIcon(qta.icon('fa5s.arrow-left'))
        self.back_btn.setToolTip("戻る")
        self.back_btn.clicked.connect(self.go_back)
        toolbar.addWidget(self.back_btn)
        
        # 進むボタン
        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(qta.icon('fa5s.arrow-right'))
        self.forward_btn.setToolTip("進む")
        self.forward_btn.clicked.connect(self.go_forward)
        toolbar.addWidget(self.forward_btn)
        
        # 更新ボタン
        self.reload_btn = QPushButton()
        self.reload_btn.setIcon(qta.icon('fa5s.sync-alt'))
        self.reload_btn.setToolTip("再読み込み")
        self.reload_btn.clicked.connect(self.reload_page)
        toolbar.addWidget(self.reload_btn)
        
        # アドレスバー
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("URLを入力またはキーワードで検索")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.url_bar)
        
        # Goボタン
        go_btn = QPushButton()
        go_btn.setIcon(qta.icon('fa5s.search'))
        go_btn.setToolTip("移動/検索")
        go_btn.clicked.connect(self.navigate_to_url)
        toolbar.addWidget(go_btn)
        
        # WebViewコンテナ（複数のWebViewを切り替える）
        self.web_container = QWidget()
        self.web_layout = QVBoxLayout(self.web_container)
        self.web_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_container)
        
        return widget
    
    def is_valid_url(self, text):
        """テキストが有効なURLかどうかを判定"""
        # URLパターンのチェック
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'|^www\.'      # www.で始まる
            r'|^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'  # domain.com形式
        )
        
        # スペースが含まれていたら検索クエリ
        if ' ' in text:
            return False
        
        # URLパターンにマッチするか
        if url_pattern.match(text):
            return True
        
        # ドット+TLD形式をチェック（例: example.com）
        if '.' in text and not text.startswith('.') and not text.endswith('.'):
            parts = text.split('.')
            if len(parts) >= 2 and len(parts[-1]) >= 2:
                return True
        
        return False
    
    def process_url_or_search(self, text):
        """URLまたは検索クエリを処理"""
        text = text.strip()
        
        if self.is_valid_url(text):
            # URLとして処理
            if not text.startswith("http://") and not text.startswith("https://"):
                text = "https://" + text
            return text
        else:
            # Google検索として処理
            search_query = quote_plus(text)
            return f"https://www.google.com/search?q={search_query}"
    
    def add_new_tab(self, url, activate=True):
        """新しいタブを追加"""
        # WebViewを作成
        web_view = QWebEngineView()
        
        # カスタムページを設定
        page = CustomWebEnginePage(self.profile, web_view)
        page.new_tab_requested.connect(lambda url: self.add_new_tab(url.toString(), activate=True))
        web_view.setPage(page)
        
        # URLを設定
        web_view.setUrl(QUrl(url))
        
        # タイトル変更時のイベント接続
        web_view.titleChanged.connect(lambda title: self.update_tab_title(web_view, title))
        web_view.urlChanged.connect(lambda url: self.update_url_bar(web_view, url))
        
        # タブアイテムを作成
        tab_item = TabItem("新しいタブ", web_view)
        
        # タブリストに追加
        self.tab_list.addItem(tab_item)
        self.tabs.append(web_view)
        
        # 新しいタブをアクティブにするか
        if activate:
            self.tab_list.setCurrentItem(tab_item)
    
    def on_tab_changed(self, current, previous):
        """タブが切り替わった時の処理"""
        if current is None:
            return
        
        # 既存のWebViewを全て非表示
        for i in reversed(range(self.web_layout.count())):
            widget = self.web_layout.itemAt(i).widget()
            if widget:
                self.web_layout.removeWidget(widget)
                widget.setParent(None)
        
        # 選択されたタブのWebViewを表示
        tab_item = current
        web_view = tab_item.web_view
        self.web_layout.addWidget(web_view)
        web_view.show()
        
        # URLバーを更新
        self.url_bar.setText(web_view.url().toString())
    
    def update_tab_title(self, web_view, title):
        """タブのタイトルを更新"""
        for i in range(self.tab_list.count()):
            item = self.tab_list.item(i)
            if isinstance(item, TabItem) and item.web_view == web_view:
                # タイトルが長い場合は切り詰める
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
            # タブアイテムとWebViewを削除
            item = self.tab_list.takeItem(current_row)
            if isinstance(item, TabItem):
                item.web_view.deleteLater()
                self.tabs.remove(item.web_view)
        elif self.tab_list.count() == 1:
            # 最後のタブの場合は警告（コンソールに出力）
            print("最後のタブは閉じられません")


def main():
    app = QApplication(sys.argv)
    browser = VerticalTabBrowser()
    browser.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
