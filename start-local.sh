#!/bin/bash

# ローカル環境でアプリケーションを起動するスクリプト

echo "=========================================="
echo "画像リサイズ高解像度化ツール - ローカル起動"
echo "=========================================="
echo ""

# バックエンドの起動
echo "📦 バックエンドを起動中..."
cd backend

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境を有効化
source venv/bin/activate

# 依存関係のインストール確認
if [ ! -f "venv/.installed" ]; then
    echo "依存関係をインストール中..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# バックエンドをバックグラウンドで起動
echo "🚀 バックエンドサーバーを起動中 (http://localhost:8000)..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "バックエンドPID: $BACKEND_PID"

# バックエンドの起動を待つ
sleep 3

# フロントエンドの起動
cd ../frontend
echo ""
echo "📦 フロントエンドを起動中..."

# 依存関係のインストール確認
if [ ! -d "node_modules" ]; then
    echo "依存関係をインストール中..."
    npm install
fi

# 環境変数の設定
export VITE_API_BASE_URL=http://localhost:8000

echo "🚀 フロントエンドサーバーを起動中 (http://localhost:5173)..."
echo ""
echo "=========================================="
echo "✅ 起動完了！"
echo "=========================================="
echo "フロントエンド: http://localhost:5173"
echo "バックエンド: http://localhost:8000"
echo ""
echo "停止するには Ctrl+C を押してください"
echo "=========================================="
echo ""

# フロントエンドを起動（フォアグラウンド）
npm run dev

# クリーンアップ
echo ""
echo "🛑 サーバーを停止中..."
kill $BACKEND_PID 2>/dev/null
echo "✅ 停止完了"

