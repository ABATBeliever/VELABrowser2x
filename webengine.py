"""
VELA Browser - WebEngine関連クラス
カスタムWebEnginePage、タブアイテム
"""

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
