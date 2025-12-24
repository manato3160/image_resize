import json
import base64
import logging
from io import BytesIO
from PIL import Image

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 規定サイズ
VERTICAL_SIZE = (1080, 1350)  # 幅×高さ
HORIZONTAL_SIZE = (1350, 1080)  # 幅×高さ

def resize_to_target(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """画像を指定サイズにリサイズ（余白なし）"""
    target_width, target_height = target_size
    original_width, original_height = image.size
    
    # アスペクト比を計算
    target_aspect = target_width / target_height
    original_aspect = original_width / original_height
    
    if abs(original_aspect - target_aspect) < 0.001:
        # アスペクト比がほぼ同じ場合、直接リサイズ
        return image.resize(target_size, Image.Resampling.LANCZOS)
    
    if original_aspect > target_aspect:
        # 元の画像がターゲットより横長 → 幅をターゲット幅に合わせてリサイズし、高さをクロップ
        scale_factor = target_width / original_width
        new_width = target_width
        new_height = int(original_height * scale_factor)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if new_height >= target_height:
            crop_top = (new_height - target_height) // 2
            return resized.crop((0, crop_top, target_width, crop_top + target_height))
        else:
            # 高さが足りない場合は、幅を拡大してからクロップ
            scale_factor = target_height / original_height
            new_height = target_height
            new_width = int(original_width * scale_factor)
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            crop_left = (new_width - target_width) // 2
            return resized.crop((crop_left, 0, crop_left + target_width, target_height))
    else:
        # 元の画像がターゲットより縦長 → 高さをターゲット高さに合わせてリサイズし、幅をクロップ
        scale_factor = target_height / original_height
        new_height = target_height
        new_width = int(original_width * scale_factor)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if new_width >= target_width:
            crop_left = (new_width - target_width) // 2
            return resized.crop((crop_left, 0, crop_left + target_width, target_height))
        else:
            # 幅が足りない場合は、高さを拡大してからクロップ
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            crop_top = (new_height - target_height) // 2
            return resized.crop((0, crop_top, target_width, crop_top + target_height))

def process_image_sync(image_data: bytes, mode: str) -> bytes:
    """同期的な画像処理（軽量版：Pillowのみ）"""
    # 画像を開く
    image = Image.open(BytesIO(image_data))
    
    # RGBに変換
    if image.mode != "RGB":
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3] if image.mode == "RGBA" else None)
            image = background
        else:
            image = image.convert("RGB")
    
    # ターゲットサイズを決定
    target_size = VERTICAL_SIZE if mode == "vertical" else HORIZONTAL_SIZE
    
    # リサイズ
    resized_image = resize_to_target(image, target_size)
    
    # 確実にターゲットサイズになっているか確認
    if resized_image.size != target_size:
        resized_image = resized_image.resize(target_size, Image.Resampling.LANCZOS)
    
    # バイトデータに変換
    output = BytesIO()
    resized_image.save(output, format="JPEG", quality=95)
    output.seek(0)
    return output.read()

def handler(req):
    """Vercel Serverless Function handler
    
    VercelのPython Functionsは、リクエストを辞書形式で受け取ります。
    しかし、実際の実装では、リクエストの形式が異なる可能性があります。
    すべての可能性を考慮して、柔軟に対応します。
    """
    try:
        # リクエストオブジェクトの形式を確認
        # VercelのPython Functionsは、リクエストを辞書形式で渡す
        if not isinstance(req, dict):
            logger.error(f"リクエストが辞書形式ではありません: {type(req)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({'success': False, 'error': 'Invalid request format'})
            }
        
        # デバッグ: リクエストオブジェクトの全体をログに出力
        logger.info(f"リクエストオブジェクトのキー: {list(req.keys())}")
        logger.info(f"リクエストオブジェクトの内容: {str(req)[:500]}")  # 最初の500文字のみ
        
        # メソッドの取得（複数の可能性を試行）
        method = None
        for key in ['method', 'httpMethod', 'REQUEST_METHOD', 'requestMethod']:
            if key in req:
                method = req[key]
                break
        
        # メソッドが取得できない場合、デフォルトでGETとする
        if not method:
            method = 'GET'
            logger.warning("メソッドが取得できませんでした。デフォルトでGETを使用します。")
        
        # ボディの取得（複数の可能性を試行）
        body_raw = None
        for key in ['body', 'payload', 'BODY', 'requestBody']:
            if key in req:
                body_raw = req[key]
                break
        
        headers = req.get('headers', {}) or req.get('HEADERS', {})
        
        logger.info(f"リクエスト受信: method={method}, body_type={type(body_raw)}, body_exists={body_raw is not None}")
        
        # CORS preflight リクエストを処理
        if method.upper() == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type',
                },
                'body': ''
            }
        
        # POSTメソッドのみ許可
        if method.upper() != 'POST':
            logger.warning(f"許可されていないメソッド: {method}")
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'Method not allowed: {method}',
                    'received_method': method,
                    'request_keys': list(req.keys())
                })
            }
        
        # ボディの処理（Vercelからは文字列または辞書で渡される）
        if body_raw is None:
            logger.error("リクエストボディが空です")
            raise ValueError('リクエストボディが空です')
        
        # ボディを文字列または辞書に変換（bytes形式はVercelから渡されない）
        if isinstance(body_raw, dict):
            data = body_raw
        elif isinstance(body_raw, str):
            data = json.loads(body_raw)
        else:
            # その他の場合は文字列に変換してからパース
            data = json.loads(str(body_raw))
        
        logger.info(f"リクエストデータ解析完了: mode={data.get('mode')}, upscale_method={data.get('upscale_method')}")
        
        # 画像データを取得（Base64エンコードされている想定）
        image_base64 = data.get('image', '')
        if not image_base64:
            logger.error("画像データが空です")
            raise ValueError('画像データが空です')
        
        image_data = base64.b64decode(image_base64)
        mode = data.get('mode', 'vertical')
        upscale_method = data.get('upscale_method', 'simple')
        
        logger.info(f"画像処理開始: mode={mode}, image_size={len(image_data)} bytes")
        
        # 画像処理（軽量版：AIアップスケールは無効）
        processed_image = process_image_sync(image_data, mode)
        
        logger.info(f"画像処理完了: processed_size={len(processed_image)} bytes")
        
        # Base64エンコードして返す
        result_base64 = base64.b64encode(processed_image).decode('utf-8')
        
        # レスポンス
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'image': result_base64,
                'content_type': 'image/jpeg'
            })
        }
        
    except Exception as e:
        logger.error(f"エラー発生: {type(e).__name__}: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            })
        }
