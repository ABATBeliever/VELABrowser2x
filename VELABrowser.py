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
import shutil
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont

from constants import (
    BROWSER_FULL_NAME, BROWSER_VERSION_SEMANTIC,
    DATA_DIR, LEGACY_DATA_DIR,
    HISTORY_DB, BOOKMARKS_DB, DOWNLOADS_DB, SESSION_FILE,
    check_db_version, check_version_stamp, VERSION_KEY,
)
from browser import VerticalTabBrowser

print(f"\n{BROWSER_FULL_NAME}")
print("\nCopyright (C) 2025-2026 ABATBeliever")
print('VELA Website     | https://abatbeliever.net/app/VELABrowser/')
print('VELA Github Repo | https://github.com/ABATBeliever/VELABrowser2x')
print(f"Data Directory: {DATA_DIR}")


# =====================================================================
# 起動前チェック: バージョン整合性
# =====================================================================

def _check_data_version_conflicts(app: QApplication) -> bool:
    """
    各 DB / session.json が現在のバージョンより新しい VELA で
    書かれていた場合に警告ダイアログを表示する。
    問題なければ True、ユーザーが中止を選んだら False を返す。
    """
    import json

    newer_sources = []

    # DB チェック
    for db_path, label in [
        (HISTORY_DB,   "閲覧履歴 (history.db)"),
        (BOOKMARKS_DB, "ブックマーク (bookmarks.db)"),
        (DOWNLOADS_DB, "ダウンロード (downloads.db)"),
    ]:
        if db_path.exists() and not check_db_version(db_path, label):
            from constants import get_db_vela_version
            newer_sources.append((label, get_db_vela_version(db_path)))

    # session.json チェック
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                sess = json.load(f)
            if not check_version_stamp(sess, "session.json"):
                newer_sources.append(("セッション (session.json)", sess.get(VERSION_KEY, "不明")))
        except Exception:
            pass

    if not newer_sources:
        return True

    # 警告ダイアログ
    detail_lines = "\n".join(f"  • {label}（バージョン {ver}）" for label, ver in newer_sources)
    msg = QMessageBox()
    msg.setWindowTitle("データバージョンの警告")
    msg.setIcon(QMessageBox.Warning)
    msg.setText(
        f"以下のデータは、現在のVELA ({BROWSER_VERSION_SEMANTIC}) より\n"
        f"新しいバージョンで保存されています。\n\n"
        f"{detail_lines}\n\n"
        f"このまま起動すると、データが失われたり\n"
        f"正しく読み込めない可能性があります。\n"
        f"開発元は、この動作に対しデータの保証を行えません。"
    )
    msg.setInformativeText("起動しますか？")
    continue_btn = msg.addButton("無視して続行", QMessageBox.AcceptRole)
    abort_btn    = msg.addButton("起動しない(推奨)",   QMessageBox.RejectRole)
    msg.setDefaultButton(abort_btn)
    msg.exec()

    return msg.clickedButton() == continue_btn


# =====================================================================
# 起動前チェック: XDG 移行
# =====================================================================

def _run_migration_if_needed(app: QApplication) -> bool:
    """
    XDG パスにデータがなく、旧パス (~/.VELA_Browser) にデータがある場合に
    移行ダイアログを表示してコピー → 再起動案内 → 終了。
    移行が発生した（再起動が必要）場合は False を返す。
    問題なければ True を返す。
    
    旧パスからXDGパスへの移行は2.1.xでのみサポートし、2.2.x以降はXDGパスを前提とする。
    """
    import platform

    # macOS・その他は XDG を使わないため移行不要
    system = platform.system().lower()
    if system not in ("linux", "windows"):
        return True

    # XDG 側にデータが既にある → 移行不要
    xdg_has_data = any([
        HISTORY_DB.exists(),
        BOOKMARKS_DB.exists(),
        SESSION_FILE.exists(),
        DOWNLOADS_DB.exists(),
    ])
    if xdg_has_data:
        return True

    # 旧パスにもデータがない → 新規インストール、そのまま続行
    if not LEGACY_DATA_DIR.exists():
        return True

    legacy_has_data = any([
        (LEGACY_DATA_DIR / "history.db").exists(),
        (LEGACY_DATA_DIR / "bookmarks.db").exists(),
        (LEGACY_DATA_DIR / "session.json").exists(),
        (LEGACY_DATA_DIR / "downloads.db").exists(),
    ])
    if not legacy_has_data:
        return True

    # --- 移行ダイアログ ---
    msg = QMessageBox()
    msg.setWindowTitle("データの移行")
    msg.setIcon(QMessageBox.Information)
    msg.setText(
        "旧バージョンのVELAのデータが見つかりました。\n\n"
        f"現在のパス	:\n  {LEGACY_DATA_DIR}\n\n"
        f"XDGのパス	:\n  {DATA_DIR}\n\n"
        "2.1.xのVELAを利用するには、データを新しい場所に移動する必要があります。\n"
        "※1 移行後にVELAを再起動してください。\n"
        "※2 移行をしても古いデータは削除されません。移行処理を行った段階でプロファイルが分岐します。"
    )
    migrate_btn = msg.addButton("移行する", QMessageBox.AcceptRole)
    cancel_btn  = msg.addButton("何もせず終了", QMessageBox.RejectRole)
    msg.setDefaultButton(migrate_btn)
    msg.exec()

    if msg.clickedButton() != migrate_btn:
        print("[INFO] Migration cancelled by user")
        return False  # 呼び出し元が終了する

    # --- コピー実行 ---
    _MIGRATE_FILES = [
        "history.db",
        "bookmarks.db",
        "downloads.db",
        "session.json",
        "downloads",   # ディレクトリ
    ]
    errors = []
    for name in _MIGRATE_FILES:
        src = LEGACY_DATA_DIR / name
        if not src.exists():
            continue
        dst = DATA_DIR / name
        try:
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            print(f"[INFO] Migration: copied {name}")
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"[ERROR] Migration failed for {name}: {e}")

    # --- 結果ダイアログ ---
    if errors:
        err_text = "\n".join(errors)
        QMessageBox.warning(
            None, "エラー",
            f"一部のファイルの移行に失敗しました:\n{err_text}\n\n"
            f"VELAを再起動してください。"
        )
    else:
        QMessageBox.information(
            None, "移行完了",
            f"データの移行が完了しました。\n\n"
            f"XDGのパス	:\n  {DATA_DIR}\n\n"
            f"VELAを再起動してください。\n"
            f"※1 旧データは {LEGACY_DATA_DIR} に残りますが、2.0.xで今後行った変更は新たに移行をしない限り2.1.xでは表示されません\n。"
            f"※2 2.0.xの利用は今後推奨されません。"
        )

    print("[INFO] Migration complete. Restart required.")
    return False  # 再起動が必要なので False


# =====================================================================
# 起動前チェック: session.json 旧形式の自動変換
# =====================================================================

def _upgrade_session_if_needed(app: QApplication) -> bool:
    """
    session.json が旧リスト形式だった場合に変換して保存し、
    再起動を促して終了する。
    変換不要なら True、再起動が必要なら False を返す。
    """
    from managers import SessionManager
    mgr = SessionManager()
    status, data = mgr.load_session()

    if status == "converted":
        # 変換したものを書き戻す
        mgr.save_session(data)
        QMessageBox.information(
            None,
            "セッションデータの最適化",
            "セッションファイルを最適化しました。\n\n"
            "VELAを再起動してください。"
        )
        print("[INFO] Session converted to new format. Restart required.")
        return False

    return True


# =====================================================================
# メイン
# =====================================================================

def main():
    """アプリケーションのメイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーション全体のスタイルシートを設定（ダークモード対策）
    app.setStyleSheet("""
        QWidget {
            background-color: #ffffff;
            color: #333333;
        }
        QMessageBox {
            background-color: #ffffff;
            color: #333333;
        }
        QMessageBox QLabel {
            color: #333333;
        }
        QMessageBox QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 6px 16px;
            border-radius: 4px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #106ebe;
        }
        QFileDialog {
            background-color: #ffffff;
            color: #333333;
        }
        QFileDialog QLabel {
            color: #333333;
        }
        QFileDialog QPushButton {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #e0e0e0;
            padding: 6px 16px;
            border-radius: 4px;
        }
        QFileDialog QTreeView, QFileDialog QListView {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #e0e0e0;
        }
        QFileDialog QTreeView::item, QFileDialog QListView::item {
            color: #333333;
        }
        QFileDialog QTreeView::item:selected, QFileDialog QListView::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        QToolTip {
            background-color: #333333;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px;
        }
    """)
    
    # フォント設定
    font = QFont()
    font.setPointSize(8)
    app.setFont(font)

    # ---- 起動前チェック（順番に実行、False で中断） ----

    # 1. XDG 移行チェック
    if not _run_migration_if_needed(app):
        sys.exit(0)

    # 2. session.json 旧形式コンバート
    if not _upgrade_session_if_needed(app):
        sys.exit(0)

    # 3. データバージョン整合性チェック（新しいVELAが書いたデータ）
    if not _check_data_version_conflicts(app):
        sys.exit(0)

    # ---- ブラウザ起動 ----
    browser = VerticalTabBrowser()
    browser.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
