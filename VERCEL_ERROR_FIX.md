# Vercel ビルドエラーの修正

## エラー内容

```
Error: Function Runtimes must have a valid version, for example `now-php@1.0.0`.
```

## 原因

`vercel.json`の`functions`設定が正しくない形式になっていました。

## 修正内容

`vercel.json`から`functions`設定を削除しました。Vercelは`api/`フォルダ内の`.py`ファイルを自動的に検出してPython Functionsとしてデプロイします。

## 修正後の設定

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

## 次のステップ

1. 変更をGitHubにプッシュ
2. Vercelで再デプロイ
3. デプロイが成功することを確認

## 確認事項

- `api/process.py`と`api/process-multiple.py`が存在することを確認
- `requirements.txt`がプロジェクトルートに存在することを確認
- Vercelのプロジェクト設定でRoot Directoryが設定されていないことを確認

