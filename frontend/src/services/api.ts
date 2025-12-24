import axios from 'axios'
import { ResizeMode, UpscaleMethod } from '../App'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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

  const formData = new FormData()
  formData.append('file', file)
  formData.append('mode', mode)
  formData.append('upscale_method', upscaleMethod)

  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/process`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
        timeout: upscaleMethod === 'ai' ? 300000 : 60000, // AI: 5分、単純: 1分
      }
    )

    // レスポンスがエラーの場合（JSONエラーレスポンスがBlobとして返される場合）
    if (response.data.type === 'application/json') {
      const errorText = await response.data.text()
      try {
        const errorData = JSON.parse(errorText)
        throw new Error(errorData.detail || '画像処理に失敗しました')
      } catch {
        throw new Error('画像処理に失敗しました')
      }
    }

    // BlobをURLに変換
    const imageUrl = URL.createObjectURL(response.data)
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

  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })
  formData.append('mode', mode)
  formData.append('upscale_method', upscaleMethod)

  try {
    const response = await axios.post<ProcessMultipleImagesResult>(
      `${API_BASE_URL}/api/process-multiple`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: upscaleMethod === 'ai' ? 600000 : 300000, // AI: 10分、単純: 5分（複数画像のため長めに）
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

