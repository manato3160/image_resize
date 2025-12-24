@echo off
REM ローカル環境でアプリケーションを起動するスクリプト（Windows用）

echo ==========================================
echo 画像リサイズ高解像度化ツール - ローカル起動
echo ==========================================
echo.

REM バックエンドの起動
echo 📦 バックエンドを起動中...
cd backend

REM 仮想環境の確認
if not exist "venv" (
    echo 仮想環境を作成中...
    python -m venv venv
)

REM 仮想環境を有効化
call venv\Scripts\activate.bat

REM 依存関係のインストール確認
if not exist "venv\.installed" (
    echo 依存関係をインストール中...
    pip install -r requirements.txt
    type nul > venv\.installed
)

REM バックエンドをバックグラウンドで起動
echo 🚀 バックエンドサーバーを起動中 (http://localhost:8000)...
start /B uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ..\backend.log 2>&1

REM バックエンドの起動を待つ
timeout /t 3 /nobreak > nul

REM フロントエンドの起動
cd ..\frontend
echo.
echo 📦 フロントエンドを起動中...

REM 依存関係のインストール確認
if not exist "node_modules" (
    echo 依存関係をインストール中...
    call npm install
)

REM 環境変数の設定
set VITE_API_BASE_URL=http://localhost:8000

echo 🚀 フロントエンドサーバーを起動中 (http://localhost:5173)...
echo.
echo ==========================================
echo ✅ 起動完了！
echo ==========================================
echo フロントエンド: http://localhost:5173
echo バックエンド: http://localhost:8000
echo.
echo 停止するには Ctrl+C を押してください
echo ==========================================
echo.

REM フロントエンドを起動（フォアグラウンド）
call npm run dev

REM クリーンアップ
echo.
echo 🛑 サーバーを停止中...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*" > nul 2>&1
echo ✅ 停止完了

