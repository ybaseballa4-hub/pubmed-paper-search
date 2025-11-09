# RT-LitSearch 🏥

整形外科クリニック向け PubMed論文要約アプリ

## 概要

RT-LitSearchは、PubMedから最新の医学論文を検索し、OpenAI GPTを使用して日本語で臨床向けの要約を生成するWebアプリケーションです。整形外科クリニックでの勉強会や日常の情報収集を効率化することを目的としています。

## 主な機能

- 🔍 **PubMed検索**: キーワードベースで最新論文を検索
- 📋 **日本語要約**: GPT-4を使用した300-500字の臨床向け要約
- 📱 **レスポンシブUI**: スマホ・PC両対応のGradioインターフェース
- 💾 **Markdown出力**: 検索結果をMarkdownファイルでダウンロード可能
- ⚡ **高速処理**: 30秒以内での結果表示

## 要約の構成

各論文について以下の構成で要約を生成します：

1. **背景・目的** (1-2文)
2. **方法・介入** (1-2文)  
3. **結果** (2-3文)
4. **臨床的示唆** (1-2文)
5. **限界・注意点** (1文)

## セットアップ

### 必要な環境

- Python 3.8以上
- OpenAI API キー
- インターネット接続

### ローカル実行

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd rt-litsearch
```

2. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

3. **環境変数の設定**
```bash
# .envファイルを作成（env_example.txtを参考）
cp env_example.txt .env

# .envファイルを編集してAPIキーを設定
OPENAI_API_KEY=your_openai_api_key_here
NIH_EMAIL=your_email@example.com  # 推奨（PubMed API用）
```

4. **アプリケーションの起動**
```bash
python app.py
```

5. **ブラウザでアクセス**
```
http://localhost:7860
```

### Hugging Face Spacesでのデプロイ

1. **新しいSpaceを作成**
   - https://huggingface.co/spaces にアクセス
   - "Create new Space"をクリック
   - SDK: "Gradio"を選択

2. **ファイルをアップロード**
   - `app.py`
   - `requirements.txt`

3. **Secretsの設定**
   - Settings → Repository secrets
   - `OPENAI_API_KEY`: OpenAI APIキー
   - `NIH_EMAIL`: メールアドレス（推奨）

4. **自動デプロイ**
   - ファイルがアップロードされると自動的にビルド・デプロイされます

## 使用方法

### 基本的な使い方

1. **検索キーワードの入力**
   - 日本語・英語どちらでも可能
   - 例: "膝OA 運動療法", "shoulder impingement exercise"

2. **取得件数の選択**
   - 1-10件の範囲で選択可能
   - デフォルト: 5件

3. **検索・要約実行**
   - ボタンをクリックして処理開始
   - 進捗状況がリアルタイムで表示

4. **結果の確認**
   - カード形式で結果を表示
   - 必要に応じてMarkdownファイルをダウンロード

### 検索のコツ

- **具体的なキーワード**: "膝関節症 運動療法" > "膝の痛み"
- **英語キーワード**: より多くの論文がヒットする可能性
- **複数キーワード**: スペース区切りでAND検索
- **専門用語**: 正確な医学用語を使用

## 技術仕様

### アーキテクチャ

```
app.py
├── PubMedSearcher     # PubMed API連携
├── PaperSummarizer    # OpenAI API連携
└── Gradio UI          # ユーザーインターフェース
```

### 使用技術

- **フロントエンド**: Gradio 4.44.0
- **バックエンド**: Python 3.8+
- **API**: PubMed E-utilities, OpenAI GPT-4
- **データ処理**: XML parsing, requests
- **デプロイ**: Hugging Face Spaces

### API制限・コスト

- **PubMed API**: 無料（レート制限あり）
- **OpenAI API**: 1論文要約あたり約1円未満
- **処理時間**: 5件の論文で約30秒

## トラブルシューティング

### よくある問題

1. **APIキーエラー**
   ```
   ⚠️ OPENAI_API_KEYが設定されていません
   ```
   → 環境変数またはSecretsでAPIキーを設定

2. **検索結果が0件**
   - キーワードを変更してみる
   - 英語キーワードを試す
   - より一般的な用語を使用

3. **要約生成エラー**
   - OpenAI APIの利用制限を確認
   - アブストラクトが存在しない論文の可能性

### ログの確認

アプリケーション実行時のコンソール出力でエラー詳細を確認できます。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssuesでお知らせください。

## 免責事項

- 本アプリケーションは教育・研究目的での使用を想定しています
- 臨床判断は必ず原著論文を確認の上で行ってください
- 要約の正確性について保証するものではありません

---

**開発者**: 整形外科クリニック向け  
**バージョン**: 1.0.0  
**最終更新**: 2025年9月




