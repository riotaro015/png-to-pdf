# PNG to PDF

連番PNGをまとめて、ひとつのPDFにする小さなデスクトップアプリです。
画像の変換はローカルで完結します。アカウントやAPIキーは不要です。

## 起動

WindowsでPython 3.10以降をインストールし、PythonをPATHに追加してください。
このフォルダーを展開し、`起動.cmd` をダブルクリックします。
PySide6がなければ初回にpipでインストールします（初回のみインターネット接続が必要）。

手動で起動する場合:

```sh
python -m pip install -r requirements.txt
python app.py
```

## 使い方

1. PNGまたはフォルダーを一覧へドロップします。追加ボタンでも選べます。
2. 一覧の上から順にPDFになります。ドラッグで順番を変えられます。
3. 「PDFに保存」で保存先を選びます。

ファイル名は数字順（1、2、10）で追加します。追加分は末尾に入り、
「数字順に整列」で全体を並べ直せます。同じファイルは重複追加しません。
フォルダー追加は直下のPNGのみが対象です。

## ページ設定

- **画像に合わせる**: 画像ごとにページの大きさを変えます。基準DPI（初期値300）で印刷サイズを決めます。元画像のDPI情報は使いません。
- **A4**: A4縦に縦横比を保って中央配置します。
- 1画像につき1ページ。透明部分と余白は白になります。
- 画像の画素数は減らしません。PNGをPDF内へロスレスで描画します。
- 読み込み失敗時は保存先PDFを置き換えません。

## 構造・配布

```text
PNG_to_PDF/
  app.py             アプリ本体（UIと変換処理）
  起動.cmd           Windows用起動ファイル
  requirements.txt   依存ライブラリはPySide6のみ
  README.md          この説明とライセンス
```

この4ファイルをまとめてZIPにすれば配布できます。
受け取った方にもPythonとPySide6が必要です。実行ファイル化や自動更新機能は含みません。
設定ファイルや専用フォルダーを作らず、PDF保存時のみ保存先に一時ファイルを作り、完了・失敗時に削除します。

見た目は指定された[お品書き一覧](https://riotaro015.github.io/circle-prep/events/yaroufes/2026-autumn/)の配色・余白・丸いカードを参考にしています。
サイトの画像・ロゴ・ソースコードは同梱していません。

## License

このアプリのオリジナルコード・ドキュメントはMIT Licenseです。
使用・改変・再配布・商用利用が可能です。再配布時は以下の表示を含めてください。
PySide6とQtはそれぞれのライセンスに従います。この許諾は第三者ライブラリには適用されません。

MIT License

Copyright (c) 2026 PNG to PDF contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
