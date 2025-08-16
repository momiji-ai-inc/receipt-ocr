## 事前準備

### APIキーの設定
.envファイルに下記のようにGemini APIキーを設定してください。

```
GEMINI_API_KEY=YOUR_API_KEY
```
### 資料の配置
`data`フォルダにPDFもしくは画像ファイルを配置。
拡張子を基準に自動で読み込み処理が行われる。

### 必要な外部ツール

PDFファイルを処理するにはpopplerが必要です。macOSの場合は下記コマンドでインストールしてください。

```bash
brew install poppler
```

### 仮想環境
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
