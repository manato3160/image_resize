# Vercelのみでデプロイする設定手順

このガイドでは、VercelのServerless Functionsを使用してバックエンドもVercelで実装する方法を説明します。

## ⚠️ 重要な注意事項

### 制約事項

1. **AIアップスケール機能は無効**: Vercel Functionsでは大きなライブラリ（Real-ESRGAN、OpenCV）が使用できないため、基本的なリサイズ機能のみが利用可能です
2. **タイムアウト制限**: 
   - 無料プラン: 10秒
   - Proプラン: 60秒
3. **メモリ制限**: 512MB
4. **処理時間**: 大きな画像や複数画像の処理に時間がかかる場合があります

### 機能

- ✅ 基本的な画像リサイズ（縦向き: 1080×1350、横向き: 1350×1080）
- ✅ 複数画像の一括処理（最大8枚）
- ✅ 余白なしリサイズ
- ❌ AIアップスケール（Vercel Functionsでは利用不可）

## デプロイ手順

### 1. Vercelのプロジェクト設定

1. Vercelダッシュボードでプロジェクトを開く
2. **Settings** → **General** に移動
3. **Root Directory**: 設定しない（プロジェクトルートを使用）
4. **Build Command**: `cd frontend && npm install && npm run build`
5. **Output Directory**: `frontend/dist`
6. **Install Command**: `cd frontend && npm install`

### 2. 環境変数の設定（不要）

Vercel Functionsを使用する場合、環境変数 `VITE_API_BASE_URL` は設定**不要**です（空文字列のまま）。

### 3. ファイル構造の確認

以下のファイルが正しく配置されているか確認：

```
project-root/
├── api/
│   ├── process.py              # 単一画像処理
│   └── process-multiple.py     # 複数画像処理
├── frontend/
│   └── ...                     # フロントエンド
├── requirements.txt            # Vercel Functions用（Pillowのみ）
└── vercel.json                 # Vercel設定
```

### 4. デプロイ

1. GitHubにプッシュ
2. Vercelが自動的にデプロイを開始
3. デプロイ完了を待つ

### 5. 動作確認

1. デプロイされたURLにアクセス
2. 画像をアップロードして処理
3. 正常にリサイズされるか確認

## トラブルシューティング

### ビルドエラー

- `requirements.txt`がプロジェクトルートにあるか確認
- Python 3.9が使用されているか確認（Vercelのデフォルト）

### 関数が動作しない

- **Functions** タブでログを確認
- APIエンドポイントが `/api/process` と `/api/process-multiple` になっているか確認

### タイムアウトエラー

- 画像サイズを小さくする
- 一度に処理する画像数を減らす
- Proプランにアップグレード（60秒タイムアウト）

### CORSエラー

- Vercel Functionsのコードで `Access-Control-Allow-Origin: *` が設定されているか確認

## ローカル開発

ローカルでVercel Functionsをテストする場合：

```bash
# Vercel CLIをインストール
npm i -g vercel

# プロジェクトルートで実行
vercel dev
```

これで `http://localhost:3000` でローカル開発が可能です。

## AIアップスケール機能が必要な場合

AIアップスケール機能が必要な場合は、以下のいずれかを選択：

1. **Railwayでバックエンドをデプロイ**: 完全な機能が利用可能
2. **外部サービスを使用**: Cloudinary、ImageKitなどの画像処理サービス

