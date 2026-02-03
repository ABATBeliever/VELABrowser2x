"""
VELA Browser - ダイアログ類
ブックマーク追加、メインダイアログ（設定・履歴・ブックマーク統合）、ダウンロードマネージャー
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QComboBox, QFrame, QMessageBox, QTabWidget,
    QTextEdit, QCheckBox, QSpinBox, QGroupBox, QScrollArea,
    QFormLayout, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QTreeWidget, QTreeWidgetItem,
    QProgressBar
)
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

from constants import STYLES, BROWSER_NAME, BROWSER_FULL_NAME, BROWSER_TARGET_Architecture, DATA_DIR, DOWNLOADS_DIR


# =====================================================================
# ブックマーク追加ダイアログ
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


# =====================================================================
# メインダイアログ（統合）
# =====================================================================

class MainDialog(QDialog):
    """メインダイアログ（ブラウザについて・設定・履歴・ブックマーク統合）"""
    
    open_url = Signal(str)
    
    def __init__(self, history_manager, bookmark_manager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.bookmark_manager = bookmark_manager
        self.setWindowTitle(f"{BROWSER_NAME}について")
        self.setMinimumSize(600, 500)
        
        # 設定を遅延インポート（循環参照回避）
        from PySide6.QtCore import QSettings
        self.settings = QSettings("ABATBeliever", "VELA")
        
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
        widget = QVBoxLayout()
        container = QWidget()
        container.setLayout(widget)
        
        widget.setContentsMargins(30, 30, 30, 30)
        widget.setSpacing(20)
        
        from constants import BROWSER_VERSION_NAME
        
        title_label = QLabel(f"<h1>{BROWSER_NAME} Praxis</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        widget.addWidget(title_label)
        
        version_label = QLabel(f"<h3>バージョン: {BROWSER_VERSION_NAME}</h3>")
        version_label.setAlignment(Qt.AlignCenter)
        widget.addWidget(version_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        widget.addWidget(line)
        
        description = QLabel(
            f"<p style='font-size: 11pt;'>{BROWSER_NAME}は、左側に縦タブを配置した<br>"
            "シンプルで使いやすいWebブラウザです。</p>"
        )
        description.setAlignment(Qt.AlignCenter)
        widget.addWidget(description)
        
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
        widget.addWidget(tech_info)
        
        copyright_label = QLabel(
            "<p style='color: #666; font-size: 9pt;'>"
            "© 2025-2026, ABATBeliever.<br>"
            "Under LGPL v3 License"
            "</p>"
        )
        copyright_label.setAlignment(Qt.AlignCenter)
        widget.addWidget(copyright_label)
        
        widget.addStretch()
        return container
    
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


# =====================================================================
# ダウンロードマネージャーダイアログ
# =====================================================================

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
