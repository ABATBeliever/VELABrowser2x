"""
VELA Browser - 定数・設定値・スタイルシート定義
"""

from pathlib import Path

# =====================================================================
# ブラウザ情報
# =====================================================================
BROWSER_NAME = "VELA"
BROWSER_CODENAME = "Praxis"
BROWSER_VERSION_SEMANTIC = "2.0.0.0a7"
BROWSER_VERSION_NAME = "2.0.0.0 Alpha7.1"
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

# =====================================================================
# スタイルシート定義
# =====================================================================
STYLES = {
    'main_window': """
        QMainWindow {
            background-color: #ffffff;
        }
    """,
    
    'toolbar': """
        QToolBar {
            background-color: #f5f5f5;
            border-bottom: 1px solid #e0e0e0;
            spacing: 5px;
            padding: 5px;
        }
        QPushButton {
            background-color: white;
            color: #333;
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
            color: #333;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 6px;
            font-size: 10pt;
        }
        QLineEdit:focus {
            border-color: #0078d4;
        }
    """,
    
    'tab_list': """
        QWidget {
            background-color: #f9f9f9;
            border-right: 1px solid #e0e0e0;
        }
        QPushButton {
            background-color: white;
            color: #333;
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
        QListWidget {
            background-color: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            outline: none;
        }
        QListWidget::item {
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
            color: #333;
        }
        QListWidget::item:selected {
            background-color: #e6f2ff;
            color: #0078d4;
        }
        QListWidget::item:hover {
            background-color: #f5f5f5;
        }
    """,
    
    'splitter': """
        QSplitter::handle {
            background-color: #e0e0e0;
            width: 1px;
        }
    """,
    
    'dialog': """
        QDialog {
            background-color: white;
        }
        QLabel {
            color: #333;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 6px;
        }
        QTableWidget, QTreeWidget {
            background-color: white;
            color: #333;
            border: 1px solid #e0e0e0;
        }
        QTableWidget::item, QTreeWidget::item {
            color: #333;
        }
        QHeaderView::section {
            background-color: #f5f5f5;
            color: #333;
            padding: 5px;
            border: 1px solid #e0e0e0;
        }
        QGroupBox {
            color: #333;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            color: #333;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QCheckBox, QRadioButton {
            color: #333;
        }
    """,
    
    'tab_widget': """
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background: white;
        }
        QTabBar::tab {
            background: #f0f0f0;
            color: #333;
            padding: 10px 20px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom: 2px solid #0078d4;
        }
    """,
    
    'button_primary': """
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
    """,
    
    'button_secondary': """
        QPushButton {
            background-color: white;
            color: #333;
            border: 1px solid #e0e0e0;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #f5f5f5;
        }
    """
}
