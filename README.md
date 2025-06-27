# Shadowverse Result Classifier

このツールは、Shadowverseのプレイ動画から自動的にスクリーンショットを取得し、試合の勝敗（勝利・敗北）をテンプレート画像に基づいて分類・保存するPythonプログラムです。

---

## 🔧 機能

- YouTube動画を360pでダウンロード
- 動画を5分ごとに分割して処理（メモリ削減のため）
- 3秒ごとにスクリーンショット取得
- 上部20%に対してテンプレートマッチング（テンプレート画像自体は既に上部20%にトリミング済み）
- 勝利・敗北・その他に分類（スコア付きで保存）
- リザルト検出後、**次の20枚のフレームをスキップ**（同じマッチのリザルトを除外するため）
- 試合数・勝利数・敗北数をCSVログに出力（動画URL付き）
- 実行のたびに前回の処理結果を初期化（CSVは保持）

---

## 📂 ディレクトリ構成

```

.
├── downloads/
│ ├── low_quality.mp4 # ダウンロードした動画（処理後に削除）
│ ├── splits/ # 5分ごとに分割した動画ファイル
│ └── screenshots/
│ ├── win/ # 勝利フレーム全体画像
│ ├── win_top/ # 勝利フレーム上部画像
│ ├── lose/ # 敗北フレーム全体画像
│ ├── lose_top/ # 敗北フレーム上部画像
│ └── non_result/ # 試合中や無関係の画像
├── win_templates_v2/ # 勝利テンプレート画像（上部20%）
├── lose_templates_v2/ # 敗北テンプレート画像（上部20%）
├── result_summary.csv # 実行ログ（動画URL・試合数・勝敗数）
├── shadowverse_sorter_final.py
└── requirements.txt

````

---

## 使い方

### 依存ライブラリのインストール

```bash
pip install -r requirements.txt
````

### テンプレートを配置
サンプルで渋谷ハル様の配信アーカイブから取得したリザルト画像を格納しています。
- `win_templates_v2/` に **勝利リザルトの上部20%画像**
- `lose_templates_v2/` に **敗北リザルトの上部20%画像**

### スクリプトの実行

```bash
python shadowverse_sorter_final.py --url "https://www.youtube.com/watch?v=xxxxxxxxxxx"
```

---

## 📝 出力ファイル：result\_summary.csv

実行のたびに以下の形式でログが追記されます：

```
動画URL,試合数,勝利数,敗北数
https://www.youtube.com/watch?v=xxxxxxx,12,7,5
```

---

## ✅ 動作条件

- Python 3.8以降
- `ffmpeg` がコマンドラインで使用可能であること（PATHに通っている）

---

## 📌 注意点

- 1回の試合につき複数のリザルト画面が保存されないよう、リザルト検出後に**次の20枚（約60秒）をスキップ**します。
- 動画や画像は実行のたびに削除されますが、`result_summary.csv` は保持されます。

---

## 📮 ライセンス

MIT License

```
