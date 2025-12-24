# ローカル環境での使用方法

Vercelでのデプロイが困難な場合、ローカル環境でアプリケーションを動作させることができます。

## 🚀 クイックスタート

### macOS/Linux

```bash
chmod +x start-local.sh
./start-local.sh
```

### Windows

```cmd
start-local.bat
```

これで自動的にバックエンドとフロントエンドが起動します。

## 📋 必要な環境

- **Python 3.11以上**
- **Node.js 18以上**
- **npm** または **yarn**

## 🔧 手動起動

### 1. バックエンドの起動

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

バックエンドは `http://localhost:8000` で起動します。

### 2. フロントエンドの起動（別のターミナル）

```bash
cd frontend
npm install

# 環境変数を設定
export VITE_API_BASE_URL=http://localhost:8000  # Windows: set VITE_API_BASE_URL=http://localhost:8000

npm run dev
```

フロントエンドは `http://localhost:5173` で起動します。

## 🌐 他の人に使ってもらう方法

### 方法1: 同じネットワーク内で共有

1. **あなたのPCのIPアドレスを確認:**
   ```bash
   # macOS/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Windows
   ipconfig
   ```
   例: `192.168.1.100`

2. **バックエンドを起動（既に起動している場合はそのまま）:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **フロントエンドの環境変数を設定:**
   ```bash
   export VITE_API_BASE_URL=http://192.168.1.100:8000
   npm run dev -- --host
   ```

4. **他の人は `http://192.168.1.100:5173` にアクセス**

### 方法2: バックエンドのみクラウドにデプロイ

バックエンドをRailwayやRenderにデプロイし、フロントエンドはローカルで起動する方法です。

#### Railwayでバックエンドをデプロイ

1. [Railway](https://railway.app)にアカウントを作成
2. 新しいプロジェクトを作成
3. GitHubリポジトリを接続、または`backend`フォルダをアップロード
4. デプロイ後、生成されたURLをコピー（例: `https://your-app.railway.app`）

#### フロントエンドの起動

```bash
cd frontend
export VITE_API_BASE_URL=https://your-app.railway.app
npm run dev
```

### 方法3: ngrokを使用してインターネット経由で共有

1. [ngrok](https://ngrok.com)をインストール
2. バックエンドを起動:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. 別のターミナルでngrokを起動:
   ```bash
   ngrok http 8000
   ```

4. ngrokが生成したURL（例: `https://xxxx.ngrok.io`）をコピー

5. フロントエンドの環境変数を設定:
   ```bash
   export VITE_API_BASE_URL=https://xxxx.ngrok.io
   npm run dev -- --host
   ```

6. 他の人はあなたのPCのIPアドレス:5173にアクセス

## 🔒 セキュリティに関する注意

- ローカルネットワークで共有する場合、ファイアウォールの設定を確認してください
- ngrokを使用する場合、無料プランではURLが定期的に変更されます
- 本番環境では適切な認証とセキュリティ対策を実装してください

## 🐛 トラブルシューティング

### バックエンドが起動しない

- Python 3.11以上がインストールされているか確認
- 仮想環境が有効化されているか確認
- ポート8000が使用されていないか確認

### フロントエンドがバックエンドに接続できない

- バックエンドが起動しているか確認
- 環境変数 `VITE_API_BASE_URL` が正しく設定されているか確認
- ブラウザのコンソールでエラーメッセージを確認

### CORSエラーが発生する

- バックエンドの`backend/app/main.py`でCORS設定を確認
- フロントエンドのURLが許可されているか確認

## 📝 その他のオプション

### Dockerを使用（オプション）

将来的にDocker Composeを使用して簡単に起動できるようにすることも可能です。

### デスクトップアプリケーション化（オプション）

ElectronやTauriを使用してデスクトップアプリケーションとして配布することも可能です。

