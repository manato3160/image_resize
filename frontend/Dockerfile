FROM node:18-alpine

WORKDIR /app

# 依存関係のインストール
COPY package*.json ./
RUN npm install

# アプリケーションコードのコピー
COPY . .

# ポートの公開
EXPOSE 5173

# 開発サーバーの起動
CMD ["npm", "run", "dev", "--", "--host"]

