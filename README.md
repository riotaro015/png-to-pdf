# PNG to PDF

連番PNGをまとめて、ひとつのPDFにする小さなアプリです。
ブラウザー版とPySide6デスクトップ版があります。
画像の変換は端末内で完結します。アカウントやAPIキーは不要です。

## ブラウザーですぐ使う

**[PNG to PDFを開く](https://riotaro015.github.io/png-to-pdf/)**

STEP 1でPNGを追加・並べ替え、STEP 2で出力設定、STEP 3で「PDFを作成」→「PDFをダウンロード」で保存します。
入力PNGの合計容量と、生成したPDFの実際の容量を保存前に比較できます。推定値ではありません。
ページ順や変換設定を変えたときは、再作成するまで出力容量をリセットします。
各PNGの「90°回転」ボタンで右へ90°ずつ回転できます。回転はプレビューとPDFに反映され、長辺・印刷サイズも回転後の向きから計算します。
ブラウザー版は `index.html` 1ファイルです。ビルドやPythonは不要です。
フォルダー追加はサブフォルダーのPNGも含みます。

### 色・サイズ・解像度の統一（ブラウザー版）

- **RGB**: ブラウザーのCanvasでsRGBへ変換し、sRGB ICCをPDFに埋め込みます。
- **グレースケール**: 8bit・1チャンネルの画像に変換します。
- **CMYK**: 手元の印刷所指定ICC（`.icc` / `.icm`）を選択し、LittleCMSでsRGBからCMYKへ変換します。変換先ICCはPDFに必ず埋め込みます。相対的色域を維持＋黒点補正を使います。ICCは同梱しません。
- **元の画素数を保持**: 拡大・縮小せず、指定dpiから各ページの印刷サイズを決めます。元画像のdpiメタデータは使いません。
- **長辺pxをそろえる**: 全ページの長辺を指定px（初期値2400）にそろえます。縦横比を保ち、短辺は比率に応じて計算します。印刷サイズは出力画素数とdpiで決まります。

余白や切り抜きは加えません。長辺2400pxなら、1000×2000pxは1200×2400px、
2000×1000pxは2400×1200pxになります。1px未満の端数は丸めます。
小さな画像も指定長辺まで拡大しますが、元にない細部は増えません。PNG内の透明部分は白になります。
RGB/CMYK/グレースケールとも8bit処理です。16bit PNGも8bitになり、元画像のピクセルやICCをそのまま保持する方式ではありません。
プレビューは元画像です。CMYKソフトプルーフ、PDF/X、トンボ、塗り足しには対応していません。
1ページは1辺16,000px・8,000万画素まで。多数の高解像度画像ではブラウザーのメモリー制限に注意してください。
Acrobatの対応範囲外になるページサイズ（各辺3〜14,400ptの範囲外）は保存前にエラーにします。

画像・ICCを送信する処理や解析・アクセス追跡コードはありません。
外部通信はページ・ライブラリ取得です。jsDelivrから固定バージョンの
[pdf-lib 1.17.1](https://github.com/Hopding/pdf-lib) と、CMYK変換時のみ
[lcms-wasm 1.0.5](https://github.com/mattdesl/lcms-wasm) を取得します。
ライブラリの取得にはインターネット接続が必要です。これらのライブラリはそれぞれMITライセンスです。

## デスクトップ版の起動

WindowsでPython 3.10以降をインストールし、PythonをPATHに追加してください。
このフォルダーを展開し、`起動.cmd` をダブルクリックします。
PySide6がなければ初回にpipでインストールします（初回のみインターネット接続が必要）。

手動で起動する場合:

```sh
python -m pip install -r requirements.txt
python app.py
```

## デスクトップ版の使い方

1. PNGまたはフォルダーを一覧へドロップします。追加ボタンでも選べます。
2. 一覧の上から順にPDFになります。ドラッグで順番を変えられます。
3. 「PDFに保存」で保存先を選びます。

ファイル名は数字順（1、2、10）で追加します。追加分は末尾に入り、
「数字順に整列」で全体を並べ直せます。同じファイルは重複追加しません。
フォルダー追加は直下のPNGのみが対象です。

## デスクトップ版のページ設定

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
  index.html         GitHub Pages用ブラウザー版（単一HTML）
```

デスクトップ版は先頭の4ファイルだけで配布できます。
受け取った方にもPythonとPySide6が必要です。実行ファイル化や自動更新機能は含みません。
デスクトップ版は設定ファイルや専用フォルダーを作らず、PDF保存時のみ保存先に一時ファイルを作り、完了・失敗時に削除します。
ブラウザー版は `index.html` だけを静的ホスティングに置けば使えます。
このリポジトリではGitHub Pagesのmainブランチ・ルート配信を使用します。ビルド設定・サーバー処理・APIキーはありません。

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
