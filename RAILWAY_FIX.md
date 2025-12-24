# Railway デプロイエラーの修正方法

## エラー内容

「Railpack でビルド プランを作成中にエラーが発生しました」というエラーが発生しています。

## 修正手順

### 1. Railwayのプロジェクト設定を確認

1. Railwayダッシュボードでプロジェクトを開く
2. **Settings** タブを開く
3. **Service Source** セクションで以下を確認：
   - **Root Directory**: `backend` に設定されているか確認
   - 設定されていない場合は `backend` に変更

### 2. 作成した設定ファイルを確認

以下のファイルが `backend` フォルダに作成されています：

- `railway.json`: Railwayの設定ファイル
- `Procfile`: 起動コマンドの定義
- `runtime.txt`: Pythonのバージョン指定
- `nixpacks.toml`: Nixpacks（Railwayのビルドシステム）の設定

### 3. GitHubにコミット・プッシュ

これらのファイルをGitHubにプッシュしてください：

```bash
cd /Users/p10516/Desktop/画像リサイズ高解像化
git add backend/railway.json backend/Procfile backend/runtime.txt backend/nixpacks.toml
git commit -m "Add Railway deployment configuration"
git push
```

### 4. Railwayで再デプロイ

1. Railwayダッシュボードで **Deployments** タブを開く
2. 最新のデプロイメントの **...** メニューから **Redeploy** を選択
3. または、GitHubにプッシュすると自動的に再デプロイが開始されます

### 5. 環境変数の設定（必要に応じて）

Railwayの **Variables** タブで、以下の環境変数を設定できます：

- `ALLOWED_ORIGINS`: CORSで許可するオリジン（カンマ区切り）
  - 例: `https://your-frontend.vercel.app,http://localhost:5173`

## トラブルシューティング

### ビルドがまだ失敗する場合

1. **Build Logs** タブで詳細なエラーメッセージを確認
2. 以下の点を確認：
   - `requirements.txt` が正しいか
   - Pythonのバージョンが正しいか（3.11を推奨）
   - 依存関係のインストールに問題がないか

### デプロイは成功するが起動しない場合

1. **Deployment Logs** タブでエラーメッセージを確認
2. ポートが正しく設定されているか確認（`$PORT`環境変数を使用）
3. 起動コマンドが正しいか確認

### 手動で設定する場合

Railwayダッシュボードで：

1. **Settings** → **Deploy** セクション
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 確認方法

デプロイが成功したら：

1. **Settings** → **Domains** でURLを確認
2. ブラウザで `https://your-app.railway.app/health` にアクセス
3. `{"status":"healthy"}` が表示されれば成功

