"""
VELA Browser - データ管理クラス群
履歴、ブックマーク、ダウンロード、セッション管理、更新チェック
"""

import sqlite3
import json
import re
from urllib.request import urlopen
from urllib.error import URLError
from packaging import version
from html import escape, unescape

from PySide6.QtCore import QThread, Signal

from constants import (
    HISTORY_DB, BOOKMARKS_DB, SESSION_FILE, DOWNLOADS_DB,
    BROWSER_VERSION_SEMANTIC, BROWSER_FULL_NAME, UPDATE_CHECK_URL
)


# =====================================================================
# 履歴管理
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


# =====================================================================
# ブックマーク管理
# =====================================================================

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


# =====================================================================
# ダウンロード管理
# =====================================================================

class DownloadManager:
    """ダウンロード管理クラス（永続化対応）"""
    
    def __init__(self):
        self.db_path = DOWNLOADS_DB
        self.downloads = []
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                url TEXT NOT NULL,
                download_path TEXT,
                total_bytes INTEGER DEFAULT 0,
                received_bytes INTEGER DEFAULT 0,
                state INTEGER DEFAULT 0,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finish_time TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("[INFO] Downloads database initialized")
    
    def add_download(self, download_item):
        """ダウンロードをメモリとDBに追加"""
        self.downloads.append(download_item)
        
        # ファイルの完全パスを取得
        download_path = download_item.downloadDirectory()
        filename = download_item.downloadFileName()
        
        # DBに保存
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO downloads (filename, url, download_path, total_bytes, received_bytes, state)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            filename,
            download_item.url().toString(),
            download_path,
            download_item.totalBytes(),
            download_item.receivedBytes(),
            download_item.state().value  # .valueで整数値を取得
        ))
        download_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"[INFO] Download added to DB with ID {download_id}: {filename}")
        
        # ダウンロード進捗の更新をDBに反映
        download_item.receivedBytesChanged.connect(
            lambda: self.update_download_progress(download_id, download_item)
        )
        download_item.stateChanged.connect(
            lambda state: self.update_download_state(download_id, download_item, state)
        )
        
        print(f"[INFO] Download started: {filename}")
    
    def update_download_progress(self, download_id, download_item):
        """ダウンロード進捗をDBに更新"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE downloads 
                SET received_bytes = ?, total_bytes = ?
                WHERE id = ?
            ''', (download_item.receivedBytes(), download_item.totalBytes(), download_id))
            conn.commit()
            conn.close()
            print(f"[DEBUG] Download progress updated: {download_id}, {download_item.receivedBytes()}/{download_item.totalBytes()}")
        except Exception as e:
            print(f"[ERROR] Failed to update download progress: {e}")
    
    def update_download_state(self, download_id, download_item, state):
        """ダウンロード状態をDBに更新"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # DownloadStateの値を取得
            if hasattr(state, 'value'):
                state_value = state.value
            else:
                state_value = int(state)
            
            # 完了時は終了時刻も記録
            if state_value == 2:  # DownloadCompleted
                cursor.execute('''
                    UPDATE downloads 
                    SET state = ?, received_bytes = ?, finish_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (state_value, download_item.receivedBytes(), download_id))
                print(f"[INFO] Download completed: {download_id}")
            else:
                cursor.execute('''
                    UPDATE downloads 
                    SET state = ?
                    WHERE id = ?
                ''', (state_value, download_id))
                print(f"[DEBUG] Download state updated: {download_id}, state={state_value}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR] Failed to update download state: {e}")
    
    def get_downloads(self):
        """現在のダウンロードリストを取得"""
        return self.downloads
    
    def get_download_history(self, limit=100):
        """ダウンロード履歴をDBから取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT filename, url, download_path, total_bytes, received_bytes, state, start_time, finish_time
            FROM downloads
            ORDER BY start_time DESC
            LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def clear_download_history(self):
        """ダウンロード履歴をクリア"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM downloads')
        conn.commit()
        conn.close()
        print("[INFO] Download history cleared")


# =====================================================================
# セッション管理
# =====================================================================

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
# 更新チェック（スレッド）
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
