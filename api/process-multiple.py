import json
import base64
import logging
from io import BytesIO
from PIL import Image
import zipfile

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
        return image.resize(target_size, Image.Resampling.LANCZOS)
    
    if original_aspect > target_aspect:
        scale_factor = target_width / original_width
        new_width = target_width
        new_height = int(original_height * scale_factor)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if new_height >= target_height:
            crop_top = (new_height - target_height) // 2
            return resized.crop((0, crop_top, target_width, crop_top + target_height))
        else:
            scale_factor = target_height / original_height
            new_height = target_height
            new_width = int(original_width * scale_factor)
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            crop_left = (new_width - target_width) // 2
            return resized.crop((crop_left, 0, crop_left + target_width, target_height))
    else:
        scale_factor = target_height / original_height
        new_height = target_height
        new_width = int(original_width * scale_factor)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if new_width >= target_width:
            crop_left = (new_width - target_width) // 2
            return resized.crop((crop_left, 0, crop_left + target_width, target_height))
        else:
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            crop_top = (new_height - target_height) // 2
            return resized.crop((0, crop_top, target_width, crop_top + target_height))

def process_image_sync(image_data: bytes, mode: str) -> bytes:
    """同期的な画像処理（軽量版：Pillowのみ）"""
    image = Image.open(BytesIO(image_data))
    
    if image.mode != "RGB":
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3] if image.mode == "RGBA" else None)
            image = background
        else:
            image = image.convert("RGB")
    
    target_size = VERTICAL_SIZE if mode == "vertical" else HORIZONTAL_SIZE
    resized_image = resize_to_target(image, target_size)
    
    if resized_image.size != target_size:
        resized_image = resized_image.resize(target_size, Image.Resampling.LANCZOS)
    
    output = BytesIO()
    resized_image.save(output, format="JPEG", quality=95)
    output.seek(0)
    return output.read()

def handler(req):
    """Vercel Serverless Function handler
    
    Vercelの公式ドキュメントに準拠:
    - リクエストは常に辞書形式で渡される
    - req.get('method') または req.get('httpMethod') でメソッドを取得
    - req.get('body') でボディを取得（文字列または辞書）
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
        method_keys_tried = []
        for key in ['method', 'httpMethod', 'REQUEST_METHOD', 'requestMethod', 'METHOD']:
            method_keys_tried.append(key)
            if key in req:
                method = req[key]
                logger.info(f"メソッドを取得: key={key}, value={method}")
                break
        
        # メソッドが取得できない場合、デフォルトでGETとする
        if not method:
            method = 'GET'
            logger.warning(f"メソッドが取得できませんでした。試行したキー: {method_keys_tried}")
        
        # ボディの取得（複数の可能性を試行）
        body_raw = None
        body_keys_tried = []
        for key in ['body', 'payload', 'BODY', 'requestBody', 'data']:
            body_keys_tried.append(key)
            if key in req:
                body_raw = req[key]
                logger.info(f"ボディを取得: key={key}, type={type(body_raw)}")
                break
        
        headers = req.get('headers', {}) or req.get('HEADERS', {})
        
        logger.info(f"複数画像処理リクエスト受信: method={method}, body_type={type(body_raw)}, body_exists={body_raw is not None}")
        
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
            req_keys = list(req.keys())
            method_keys_tried = ['method', 'httpMethod', 'REQUEST_METHOD', 'requestMethod', 'METHOD']
            body_keys_tried = ['body', 'payload', 'BODY', 'requestBody', 'data']
            error_response = {
                'success': False,
                'error': f'Method not allowed: {method}',
                'received_method': method,
                'request_keys': req_keys,
                'method_keys_tried': method_keys_tried,
                'body_keys_tried': body_keys_tried,
                'request_sample': {k: str(v)[:100] for k, v in list(req.items())[:5]}  # 最初の5つのキーと値のサンプル
            }
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps(error_response, ensure_ascii=False)
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
        
        # 複数画像データを取得
        images_data = data.get('images', [])
        mode = data.get('mode', 'vertical')
        upscale_method = data.get('upscale_method', 'simple')
        
        logger.info(f"複数画像処理開始: 画像数={len(images_data)}, mode={mode}")
        
        processed_images = []
        errors = []
        
        for idx, img_data in enumerate(images_data):
            try:
                image_base64 = img_data.get('image', '')
                filename = img_data.get('filename', f'image_{idx+1}.jpg')
                
                if not image_base64:
                    raise ValueError(f"画像データが空です: {filename}")
                
                logger.info(f"画像処理中 ({idx+1}/{len(images_data)}): {filename}")
                
                # Base64デコード
                image_data_bytes = base64.b64decode(image_base64)
                
                # 画像処理
                processed_image = process_image_sync(image_data_bytes, mode)
                
                # Base64エンコード
                result_base64 = base64.b64encode(processed_image).decode('utf-8')
                
                processed_images.append({
                    'filename': filename,
                    'data': f'data:image/jpeg;base64,{result_base64}',
                    'content_type': 'image/jpeg'
                })
                
                logger.info(f"画像処理完了 ({idx+1}/{len(images_data)}): {filename}")
            except Exception as e:
                error_msg = f"{img_data.get('filename', f'ファイル{idx+1}')}: {str(e)}"
                logger.error(f"画像処理エラー: {error_msg}")
                errors.append(error_msg)
        
        if len(processed_images) == 0:
            logger.error("すべての画像の処理に失敗しました")
            raise Exception("すべての画像の処理に失敗しました")
        
        logger.info(f"ZIPファイル作成中: {len(processed_images)}枚の画像")
        
        # ZIPファイルも作成
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for img in processed_images:
                img_bytes = base64.b64decode(img['data'].split(',')[1])
                zip_file.writestr(img['filename'], img_bytes)
        zip_buffer.seek(0)
        zip_base64 = base64.b64encode(zip_buffer.read()).decode('utf-8')
        
        logger.info(f"複数画像処理完了: 成功={len(processed_images)}, エラー={len(errors)}")
        
        # レスポンス
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'images': processed_images,
                'zip_data': f'data:application/zip;base64,{zip_base64}',
                'zip_filename': 'processed_images.zip',
                'errors': errors if errors else None
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
