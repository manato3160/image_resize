# 画像リサイズ高解像度化ツール

ユーザーがアップロードした画像を規定のサイズ（縦：1080×1350px、横：1350×1080px）にリサイズし、高解像度化するWebアプリケーションです。

## 機能

- 画像のアップロード（ドラッグ&ドロップ対応）
- 2つのリサイズモード
  - 縦向き: 1080 × 1350px
  - 横向き: 1350 × 1080px
- 2つの高解像度化方法
  - 単純リサイズ: 高速処理
  - AIアップスケール: 高品質（Real-ESRGAN使用）
- 処理済み画像のプレビューとダウンロード

## 技術スタック

### フロントエンド
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Axios

### バックエンド
- Python 3.11+
- FastAPI
- Pillow (PIL)
- Real-ESRGAN (オプション)

## クイックスタート（ローカル環境）

### 方法1: Docker Compose（最も簡単）

```bash
docker-compose up
```

- フロントエンド: http://localhost:5173
- バックエンド: http://localhost:8000

詳細は [DOCKER_USAGE.md](./DOCKER_USAGE.md) を参照してください。

### 方法2: 自動起動スクリプト

**macOS/Linux:**
```bash
chmod +x start-local.sh
./start-local.sh
```

**Windows:**
```cmd
start-local.bat
```

これでバックエンドとフロントエンドが自動的に起動します。

### 方法3: 手動起動

#### バックエンド

1. Python仮想環境を作成・有効化:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

**注意**: Real-ESRGANのインストールに失敗する場合:
- AIアップスケール機能は利用できませんが、単純リサイズ機能は正常に動作します
- Real-ESRGANを手動でインストールする場合:
  ```bash
  pip install git+https://github.com/xinntao/Real-ESRGAN.git
  ```

3. サーバーを起動:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### フロントエンド

**別のターミナルで:**

1. 依存関係をインストール:
```bash
cd frontend
npm install
```

2. 環境変数を設定（ローカル用）:
```bash
# macOS/Linux
export VITE_API_BASE_URL=http://localhost:8000

# Windows
set VITE_API_BASE_URL=http://localhost:8000
```

3. 開発サーバーを起動:
```bash
npm run dev
```

4. ブラウザで `http://localhost:5173` を開く

## 他の人に使ってもらう方法

詳細は [LOCAL_USAGE.md](./LOCAL_USAGE.md) を参照してください。

### 方法1: ローカルネットワークで共有

同じネットワーク内の他の人に使ってもらう場合：

1. **バックエンドの起動時にホストを指定:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **フロントエンドの環境変数を設定:**
   ```bash
   # あなたのPCのIPアドレスを確認（例: 192.168.1.100）
   # macOS/Linux
   export VITE_API_BASE_URL=http://192.168.1.100:8000
   
   # Windows
   set VITE_API_BASE_URL=http://192.168.1.100:8000
   ```

3. **フロントエンドを起動:**
   ```bash
   cd frontend
   npm run dev -- --host
   ```

4. **他の人は `http://あなたのIPアドレス:5173` にアクセス**

### 方法2: バックエンドをクラウドにデプロイ（推奨）

バックエンドのみをクラウドにデプロイし、フロントエンドはローカルで起動する方法：

#### バックエンドのデプロイ（Railway推奨）

1. [Railway](https://railway.app)にアカウントを作成
2. 新しいプロジェクトを作成
3. GitHubリポジトリを接続、または`backend`フォルダをアップロード
4. デプロイ後、生成されたURLをコピー（例: `https://your-app.railway.app`）

#### フロントエンドの起動

```bash
cd frontend
export VITE_API_BASE_URL=https://your-app.railway.app  # バックエンドのURL
npm run dev
```

### 方法3: ngrokを使用してインターネット経由で共有

1. [ngrok](https://ngrok.com)をインストール
2. バックエンドを起動
3. `ngrok http 8000` を実行
4. 生成されたURLをフロントエンドの環境変数に設定

詳細は [LOCAL_USAGE.md](./LOCAL_USAGE.md) を参照してください。

### 方法4: 完全にローカルで動作（オフライン対応）

インターネット接続なしで動作させる場合：

1. このリポジトリをクローンまたはダウンロード
2. 上記の「クイックスタート」の手順に従って起動
3. すべての処理はローカルで完結します

## 使用方法

1. 画像をアップロード（ドラッグ&ドロップまたはクリック）
2. リサイズモードを選択（縦向き/横向き）
3. 高解像度化方法を選択（単純リサイズ/AIアップスケール）
4. 「画像を処理」ボタンをクリック
5. 処理済み画像をプレビューしてダウンロード

## 注意事項

- 対応画像形式: JPEG, PNG, WebP
- 最大ファイルサイズ: 50MB
- AIアップスケールは処理に時間がかかる場合があります（最大5分）
- Real-ESRGANのモデルは初回実行時に自動ダウンロードされます

## トラブルシューティング

### バックエンドが起動しない
- Python 3.11以上がインストールされているか確認
- 仮想環境が有効化されているか確認
- 依存関係が正しくインストールされているか確認

### 画像処理が失敗する
- 画像ファイルが破損していないか確認
- ファイルサイズが50MB以下か確認
- バックエンドのログを確認

### AIアップスケールが動作しない
- Real-ESRGANのインストールに失敗している可能性があります
- その場合、単純リサイズに自動的にフォールバックされます

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

