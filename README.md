# VELA Browser 2.x - Vital Environment for Liberty Access

![License](https://img.shields.io/badge/license-LGPLv3-blue.svg)
![Version](https://img.shields.io/badge/version-2.0.0.0-green.svg)
![Version](https://img.shields.io/badge/Language-Python-yellow.svg)

---

## 概要

VELA（Vital Environment for Liberty Access）は、PySide6 と QtWebEngine を利用して開発された、軽量で拡張性の高いマルチプラットフォームブラウザです。  
**プライバシー配慮、移植性、必要な機能に特化**

※このリポジトリは2.x用です。2.xは現在Alpha版です。1.xは[こちら](https://github.com/ABATBeliever/VELA-Browser/)

---

## 入手

現在Alphaであり、使用は推奨しません。

1.xをご利用ください。

---

## 主要機能

- Chromium ベースのレンダリング（QtWebEngine）
- タブブラウジング（起動時の復元機能付き）
- ブラウザレベルのトラッキング防止、広告ブロック（EasyList などの定義ファイルを利用可能）
- プライベートブラウジングモード
- UserAgent のランダム化（最新近辺の Microsoft Edge に偽装、起動ごとに変化）
- ブックマーク / 履歴のエクスポート・インポート
- デベロップツールあり
- 水平タブをネイティブサポート

---

## 動作環境・対応状況

| OS                      | アーキテクチャ | 対応 |
|-------------------------|---------------|------|
| Windows 11 以降          | x64           |対応済|
| Linux 系                 | x64           |対応済|
| Raspberry Pi Trixie 以降 | aarch64       |x|
| macOS | aarch64       |サードパーティによる対応|

※arm版Windows、macOS、及びLinuxは今後対応予定です

---

## ライセンス

VELA Browser は **GNU Lesser General Public License (LGPL)** に基づいて配布されています。  

---

## クレジット / サードパーティライブラリ

- Qt (Qt Company)  
- QtAwesome  
- QtWebEngine  

各ライブラリのライセンスはそれぞれの配布元に準拠します。

---

## 連絡先

- **作者:** ABATBeliever  
- **リポジトリ:** [https://github.com/ABATBeliever/VELA-Browser](https://github.com/ABATBeliever/VELABrowser2x)  
- **問題報告:** [https://github.com/ABATBeliever/VELA-Browser/issues](https://github.com/ABATBeliever/VELABrowser2x/issues)  
- **公式ページ:** [https://abatbeliever.net/app/VELABrowser/](https://abatbeliever.net/app/VELABrowser/)
