# Vercel 404エラーの修正方法

## 問題

Vercelにデプロイした際に404エラーが表示される場合、以下の原因が考えられます：

1. **バックエンドAPIがデプロイされていない**
2. **環境変数が設定されていない**
3. **Vercelの設定が正しくない**

## 即座に修正する手順

### ステップ1: Vercelのプロジェクト設定を確認

1. Vercelダッシュボードでプロジェクトを開く
2. **Settings** → **General** に移動
3. **Root Directory** が `frontend` に設定されているか確認
4. 設定されていない場合は `frontend` に変更して保存

### ステップ2: 環境変数を設定

1. Vercelダッシュボードで **Settings** → **Environment Variables** に移動
2. 以下の環境変数を追加：
   - **Name**: `VITE_API_BASE_URL`
   - **Value**: バックエンドのURL（例: `https://your-backend.railway.app`）
   - **Environment**: Production, Preview, Development すべてにチェック
3. **Save** をクリック

### ステップ3: バックエンドをデプロイ（まだの場合）

バックエンドがデプロイされていない場合、以下のいずれかでデプロイしてください：

#### Railway（最も簡単）

1. https://railway.app にアクセス
2. 新しいプロジェクトを作成
3. GitHubリポジトリを接続、または`backend`フォルダをアップロード
4. 自動的にデプロイされます
5. 生成されたURLをコピー（例: `https://your-app.railway.app`）

#### Render

1. https://render.com にアクセス
2. 新しいWeb Serviceを作成
3. `backend`フォルダを指定
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### ステップ4: CORS設定を更新

バックエンドの`backend/app/main.py`で、VercelのURLをCORS設定に追加：

```python
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://your-app.vercel.app",  # ここにVercelのURLを追加
]
```

### ステップ5: 再デプロイ

1. Vercelで **Deployments** タブを開く
2. 最新のデプロイメントの **...** メニューから **Redeploy** を選択
3. 環境変数の変更を反映するため、**Use existing Build Cache** のチェックを外す

## 確認方法

1. ブラウザでVercelのURLにアクセス
2. 開発者ツール（F12）を開く
3. **Console**タブでエラーを確認
4. **Network**タブでAPIリクエストが正しいURLに送信されているか確認

## よくある問題

### 環境変数が反映されない

- 環境変数を追加した後、必ず再デプロイが必要です
- ブラウザのキャッシュをクリアしてください

### CORSエラーが発生する

- バックエンドのCORS設定にフロントエンドのURLが含まれているか確認
- バックエンドを再デプロイしてください

### バックエンドに接続できない

- バックエンドのURLが正しいか確認
- バックエンドが起動しているか確認（`/health`エンドポイントにアクセス）

