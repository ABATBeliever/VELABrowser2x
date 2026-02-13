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
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from constants import BROWSER_FULL_NAME, DATA_DIR
from browser import VerticalTabBrowser

print(f"\n{BROWSER_FULL_NAME}")
print("\nCopyright (C) 2025-2026 ABATBeliever")
print('VELA Website     | https://abatbeliever.net/app/VELABrowser/')
print('VELA Github Repo | https://github.com/ABATBeliever/VELABrowser2x')
print(f"Data Directory: {DATA_DIR}")


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
    font.setPointSize(9)
    app.setFont(font)
    
    # ブラウザウィンドウを作成して表示
    browser = VerticalTabBrowser()
    browser.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
