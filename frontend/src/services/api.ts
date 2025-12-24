import axios from 'axios'
import { ResizeMode, UpscaleMethod } from '../App'

// Vercel Functionsを使用する場合は、環境変数が設定されていない場合は相対パスを使用
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 最大ファイルサイズ: 50MB
const MAX_FILE_SIZE = 50 * 1024 * 1024

export async function processImage(
  file: File,
  mode: ResizeMode,
  upscaleMethod: UpscaleMethod
): Promise<string> {
  // ファイルサイズチェック
  if (file.size > MAX_FILE_SIZE) {
    throw new Error(
      `ファイルサイズが大きすぎます。最大${MAX_FILE_SIZE / (1024 * 1024)}MBまで対応しています。`
    )
  }

  // ファイルタイプチェック
  if (!file.type.startsWith('image/')) {
    throw new Error('画像ファイルを選択してください')
  }

  // ファイルをBase64エンコード
  const fileBase64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // data:image/...;base64, の部分を除去
      const base64 = result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })

  // Vercel Functions用のJSON形式で送信
  const requestData = {
    image: fileBase64,
    mode: mode,
    upscale_method: upscaleMethod
  }

  try {
    const response = await axios.post<{ success: boolean; image?: string; error?: string; content_type?: string }>(
      `${API_BASE_URL}/api/process`,
      requestData,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30秒（Vercel Functionsの制限を考慮）
      }
    )

    if (!response.data.success || !response.data.image) {
      throw new Error(response.data.error || '画像処理に失敗しました')
    }

    // Base64データをBlob URLに変換
    const imageUrl = `data:${response.data.content_type || 'image/jpeg'};base64,${response.data.image}`
    return imageUrl
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        // エラーレスポンスがBlobの場合
        if (error.response.data instanceof Blob) {
          try {
            const errorText = await error.response.data.text()
            const errorData = JSON.parse(errorText)
            throw new Error(errorData.detail || '画像処理に失敗しました')
          } catch {
            throw new Error('画像処理に失敗しました')
          }
        }
        // 通常のエラーレスポンス
        const errorMessage =
          error.response.data?.detail ||
          error.response.data?.message ||
          `エラー: ${error.response.status} ${error.response.statusText}`
        throw new Error(errorMessage)
      } else if (error.request) {
        throw new Error(
          'サーバーに接続できませんでした。APIエンドポイントを確認してください。'
        )
      } else if (error.code === 'ECONNABORTED') {
        throw new Error('リクエストがタイムアウトしました。画像が大きすぎる可能性があります。')
      }
    }
    if (error instanceof Error) {
      throw error
    }
    throw new Error('予期しないエラーが発生しました')
  }
}

export interface ProcessedImage {
  filename: string
  data: string // Base64 data URL
  content_type: string
}

export interface ProcessMultipleImagesResult {
  images: ProcessedImage[]
  zip_data: string // Base64 data URL for ZIP
  zip_filename: string
  errors?: string[] | null
}

export async function processMultipleImages(
  files: File[],
  mode: ResizeMode,
  upscaleMethod: UpscaleMethod
): Promise<ProcessMultipleImagesResult> {
  // ファイル数チェック
  if (files.length === 0) {
    throw new Error('画像を選択してください')
  }

  if (files.length > 8) {
    throw new Error('画像は最大8枚までアップロードできます')
  }

  // 各ファイルの検証
  const maxSize = 50 * 1024 * 1024
  for (const file of files) {
    if (file.size > maxSize) {
      throw new Error(
        `${file.name}: ファイルサイズが大きすぎます。最大${maxSize / (1024 * 1024)}MBまで対応しています。`
      )
    }

    if (!file.type.startsWith('image/')) {
      throw new Error(`${file.name}: 画像ファイルを選択してください`)
    }
  }

  // すべてのファイルをBase64エンコード
  const imagesData = await Promise.all(
    files.map(async (file) => {
      const fileBase64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          const result = reader.result as string
          const base64 = result.split(',')[1]
          resolve(base64)
        }
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
      return {
        image: fileBase64,
        filename: file.name
      }
    })
  )

  // Vercel Functions用のJSON形式で送信
  const requestData = {
    images: imagesData,
    mode: mode,
    upscale_method: upscaleMethod
  }

  try {
    const response = await axios.post<ProcessMultipleImagesResult>(
      `${API_BASE_URL}/api/process-multiple`,
      requestData,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 60000, // 60秒（Vercel Functionsの制限を考慮）
      }
    )

    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        // 通常のエラーレスポンス
        const errorMessage =
          error.response.data?.detail ||
          error.response.data?.message ||
          `エラー: ${error.response.status} ${error.response.statusText}`
        throw new Error(errorMessage)
      } else if (error.request) {
        throw new Error(
          'サーバーに接続できませんでした。バックエンドが起動しているか確認してください。'
        )
      } else if (error.code === 'ECONNABORTED') {
        throw new Error('リクエストがタイムアウトしました。画像が大きすぎる可能性があります。')
      }
    }
    if (error instanceof Error) {
      throw error
    }
    throw new Error('予期しないエラーが発生しました')
  }
}

