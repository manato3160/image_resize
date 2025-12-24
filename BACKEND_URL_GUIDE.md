# バックエンドURLの確認方法

バックエンドをデプロイしたサービスによって、URLの確認方法が異なります。

## Railway の場合

1. https://railway.app にログイン
2. プロジェクトを選択
3. デプロイされたサービス（Service）をクリック
4. **Settings** タブを開く
5. **Domains** セクションに表示されているURLをコピー
   - 例: `https://your-app.railway.app`
6. または、**Deployments** タブで最新のデプロイメントを確認し、**View Logs** からURLを確認

### Railwayでカスタムドメインを設定する場合

1. **Settings** → **Domains** でカスタムドメインを追加できます
2. または、自動生成された `.railway.app` のURLを使用できます

## Render の場合

1. https://render.com にログイン
2. ダッシュボードでWeb Serviceを選択
3. 上部に表示されているURLをコピー
   - 例: `https://your-app.onrender.com`
4. または、**Settings** → **Environment** で確認できます

## Fly.io の場合

1. ターミナルで以下を実行：
   ```bash
   fly status
   ```
2. または、https://fly.io のダッシュボードで確認
3. URLは通常 `https://your-app.fly.dev` の形式

## Heroku の場合

1. https://dashboard.heroku.com にログイン
2. アプリを選択
3. **Settings** タブで **Domains** セクションを確認
4. または、**Open app** ボタンでURLを確認

## バックエンドがまだデプロイされていない場合

バックエンドをデプロイする必要があります。最も簡単な方法は **Railway** です：

### Railwayでデプロイする手順

1. https://railway.app にアクセスしてアカウントを作成（GitHubアカウントでログイン可能）
2. **New Project** をクリック
3. **Deploy from GitHub repo** を選択（推奨）または **Empty Project** を選択
4. GitHubリポジトリを接続する場合：
   - リポジトリを選択
   - **Add Service** → **GitHub Repo** を選択
   - `backend` フォルダを指定
5. または、**Empty Project** を選択して手動で設定：
   - **Add Service** → **GitHub Repo** または **Empty Service**
   - `backend` フォルダをアップロード
6. Railwayが自動的に検出してデプロイを開始
7. デプロイ完了後、**Settings** → **Domains** でURLを確認

### Railwayの設定（必要な場合）

Railwayが自動検出しない場合、以下を設定：

1. **Settings** → **Generate Domain** をクリックしてドメインを生成
2. **Variables** タブで環境変数を設定（通常は不要）
3. **Deploy** タブでデプロイログを確認

## バックエンドURLの確認方法（共通）

デプロイ後、以下の方法でバックエンドが動作しているか確認できます：

### 1. ヘルスチェックエンドポイント

ブラウザで以下のURLにアクセス：
```
https://your-backend-url.com/health
```

正常に動作している場合、以下のJSONが返されます：
```json
{"status":"healthy"}
```

### 2. APIルートエンドポイント

```
https://your-backend-url.com/
```

正常に動作している場合、以下のJSONが返されます：
```json
{"message":"画像リサイズ高解像度化API"}
```

### 3. APIドキュメント

```
https://your-backend-url.com/docs
```

FastAPIの自動生成されたAPIドキュメントが表示されます。

## トラブルシューティング

### URLにアクセスできない

- デプロイが完了しているか確認（数分かかる場合があります）
- ログを確認してエラーがないか確認
- ポート設定が正しいか確認（RailwayやRenderは自動的に`$PORT`環境変数を使用）

### 404エラーが表示される

- バックエンドのルートパス（`/`）にアクセスして動作確認
- CORS設定を確認

### デプロイが失敗する

- `requirements.txt`が正しいか確認
- ログを確認してエラーメッセージを確認
- Pythonのバージョンが正しいか確認（Railwayは自動検出）

