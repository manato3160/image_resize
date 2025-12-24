# デプロイメントガイド

このアプリケーションはフロントエンドとバックエンドが分離された構成です。

## デプロイ手順

### 1. バックエンドのデプロイ

バックエンド（FastAPI）は以下のいずれかのサービスにデプロイしてください：

#### オプションA: Railway（推奨）

1. [Railway](https://railway.app)にアカウントを作成
2. 新しいプロジェクトを作成
3. GitHubリポジトリを接続、または`backend`フォルダをアップロード
4. 環境変数は自動的に検出されます
5. デプロイ後、生成されたURLをコピー（例: `https://your-app.railway.app`）

#### オプションB: Render

1. [Render](https://render.com)にアカウントを作成
2. 新しいWeb Serviceを作成
3. `backend`フォルダを指定
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. デプロイ後、生成されたURLをコピー

#### オプションC: Fly.io

1. [Fly.io](https://fly.io)にアカウントを作成
2. `backend`フォルダで`fly launch`を実行
3. デプロイ後、生成されたURLをコピー

### 2. フロントエンドのデプロイ（Vercel）

1. [Vercel](https://vercel.com)にアカウントを作成
2. プロジェクトをインポート
3. **Root Directory**: `frontend`に設定
4. **Build Command**: `npm run build`
5. **Output Directory**: `dist`
6. **Environment Variables**に以下を追加：
   - `VITE_API_BASE_URL`: バックエンドのURL（例: `https://your-backend.railway.app`）
7. デプロイ

### 3. CORS設定の確認

バックエンドの`backend/app/main.py`で、フロントエンドのURLをCORS設定に追加してください：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://your-frontend.vercel.app"  # VercelのURLを追加
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## トラブルシューティング

### 404エラーが表示される

- バックエンドが正しくデプロイされているか確認
- 環境変数`VITE_API_BASE_URL`が正しく設定されているか確認
- ブラウザの開発者ツールでネットワークエラーを確認

### CORSエラーが発生する

- バックエンドのCORS設定にフロントエンドのURLが含まれているか確認

### 画像処理が失敗する

- バックエンドのログを確認
- ファイルサイズ制限を確認（最大50MB）

