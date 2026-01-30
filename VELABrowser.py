# VELA2 Alpha1
# LGPL v3

import sys
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLineEdit, QListWidget,
    QListWidgetItem, QSplitter, QToolBar
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QIcon, QAction


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
        self.tabs = []  # WebViewのリスト
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("VELA2.x Alpha1")
        self.setGeometry(100, 100, 1200, 800)
        
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
        
    def create_tab_list(self):
        """左側のタブリストを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 新規タブボタン
        new_tab_btn = QPushButton("+")
        new_tab_btn.clicked.connect(lambda: self.add_new_tab("https://www.google.com"))
        layout.addWidget(new_tab_btn)
        
        # タブリスト
        self.tab_list = QListWidget()
        self.tab_list.currentItemChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_list)
        
        # タブを閉じるボタン
        close_tab_btn = QPushButton("-")
        close_tab_btn.clicked.connect(self.close_current_tab)
        layout.addWidget(close_tab_btn)
        
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
        self.back_btn = QPushButton("←")
        self.back_btn.clicked.connect(self.go_back)
        toolbar.addWidget(self.back_btn)
        
        # 進むボタン
        self.forward_btn = QPushButton("→")
        self.forward_btn.clicked.connect(self.go_forward)
        toolbar.addWidget(self.forward_btn)
        
        # 更新ボタン
        self.reload_btn = QPushButton("⟳")
        self.reload_btn.clicked.connect(self.reload_page)
        toolbar.addWidget(self.reload_btn)
        
        # アドレスバー
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.url_bar)
        
        # Goボタン
        go_btn = QPushButton("Go")
        go_btn.clicked.connect(self.navigate_to_url)
        toolbar.addWidget(go_btn)
        
        # WebViewコンテナ（複数のWebViewを切り替える）
        self.web_container = QWidget()
        self.web_layout = QVBoxLayout(self.web_container)
        self.web_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_container)
        
        return widget
    
    def add_new_tab(self, url):
        """新しいタブを追加"""
        # WebViewを作成
        web_view = QWebEngineView()
        web_view.setUrl(QUrl(url))
        
        # タイトル変更時のイベント接続
        web_view.titleChanged.connect(lambda title: self.update_tab_title(web_view, title))
        web_view.urlChanged.connect(lambda url: self.update_url_bar(web_view, url))
        
        # タブアイテムを作成
        tab_item = TabItem("新しいタブ", web_view)
        
        # タブリストに追加
        self.tab_list.addItem(tab_item)
        self.tabs.append(web_view)
        
        # 新しいタブを選択
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
        """URLバーのアドレスに移動"""
        current_item = self.tab_list.currentItem()
        if current_item and isinstance(current_item, TabItem):
            url = self.url_bar.text()
            # http(s)://が無い場合は追加
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
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
            # 最後のタブの場合は警告
            print("最後のタブは閉じられません")

def main():
    app = QApplication(sys.argv)
    browser = VerticalTabBrowser()
    browser.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
