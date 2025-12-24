# Dockerを使用した起動方法

DockerとDocker Composeを使用して、簡単にアプリケーションを起動できます。

## 📋 必要な環境

- **Docker Desktop** がインストールされていること
- **Docker Compose** が利用可能であること

## 🚀 起動方法

### 1. Docker Composeで起動

```bash
docker-compose up
```

初回起動時は、イメージのビルドと依存関係のインストールに時間がかかります。

### 2. アクセス

- **フロントエンド**: http://localhost:5173
- **バックエンド**: http://localhost:8000

### 3. 停止

```bash
docker-compose down
```

## 🔧 個別にビルド・起動

### バックエンドのみ

```bash
cd backend
docker build -t image-resize-backend .
docker run -p 8000:8000 image-resize-backend
```

### フロントエンドのみ

```bash
cd frontend
docker build -t image-resize-frontend .
docker run -p 5173:5173 -e VITE_API_BASE_URL=http://localhost:8000 image-resize-frontend
```

## 📝 注意事項

- Dockerを使用する場合、開発時のホットリロードが有効になっています
- 本番環境では、適切なビルドコマンドを使用してください
- ボリュームマウントにより、コードの変更が即座に反映されます

## 🐛 トラブルシューティング

### ポートが既に使用されている

```bash
# ポートを変更する場合、docker-compose.ymlを編集
ports:
  - "8001:8000"  # ホスト側のポートを変更
```

### イメージの再ビルド

```bash
docker-compose build --no-cache
docker-compose up
```

### ログの確認

```bash
docker-compose logs -f
```

