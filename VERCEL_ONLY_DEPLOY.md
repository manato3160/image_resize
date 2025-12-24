# Vercelのみでデプロイする方法

VercelのServerless Functionsを使用してバックエンドもVercelで実装する方法です。

## 制約事項

⚠️ **重要な注意点**:

1. **処理時間の制限**: Vercelの無料プランでは10秒、Proプランでも60秒のタイムアウトがあります
2. **メモリ制限**: 512MBのメモリ制限があります
3. **依存関係のサイズ**: 大きなライブラリ（OpenCV、Real-ESRGAN）はデプロイサイズを超える可能性があります
4. **コールドスタート**: 初回リクエスト時にライブラリの読み込みに時間がかかります

## 推奨アプローチ

### オプション1: 軽量版（Pillowのみ使用）

AIアップスケール機能を除き、基本的なリサイズ機能のみを実装します。

### オプション2: 外部サービスを使用

画像処理を外部サービス（Cloudinary、ImageKitなど）に委譲します。

### オプション3: ハイブリッド

- 基本的なリサイズ: Vercel Functions
- AIアップスケール: 別サービス（Railwayなど）

## 実装方法（オプション1: 軽量版）

### 1. Vercel Functionsの構造

```
project-root/
├── api/
│   └── process.py          # Vercel Serverless Function
├── backend/
│   └── app/
│       └── services/
│           └── image_processor.py  # 画像処理ロジック
├── frontend/
│   └── ...                 # フロントエンド
└── requirements.txt        # Vercel用の依存関係
```

### 2. requirements.txtの作成

Vercel用に軽量な依存関係のみを含めます：

```txt
fastapi==0.104.1
pillow==10.1.0
python-multipart==0.0.6
```

### 3. APIエンドポイントの実装

`api/process.py` にVercel Functionを実装します。

### 4. フロントエンドの修正

API呼び出しをVercel Functions用に変更します。

## より現実的な解決策

Vercelのみで完結させる場合、以下のアプローチが推奨されます：

### 1. フロントエンドのみVercelにデプロイ

- フロントエンド: Vercel
- バックエンド: Railway（無料プランあり）またはRender（無料プランあり）

### 2. 外部画像処理サービスを使用

- Cloudinary（無料プランあり）
- ImageKit（無料プランあり）
- Imgix

これらのサービスは画像リサイズをAPIで提供しており、Vercel Functionsから呼び出すことができます。

## 実装の選択

どのアプローチで進めますか？

1. **軽量版（Pillowのみ）**: 基本的なリサイズのみ、AIアップスケールなし
2. **外部サービス連携**: Cloudinaryなどと連携
3. **ハイブリッド**: 基本機能はVercel、AI機能は別サービス

