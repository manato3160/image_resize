import json
import base64
import logging
from io import BytesIO
from PIL import Image
import zipfile
from http.server import BaseHTTPRequestHandler

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


class handler(BaseHTTPRequestHandler):
    """
    Vercel Serverless Function handler for multiple images
    
    Vercelの公式ドキュメントに準拠したBaseHTTPRequestHandlerクラス形式
    https://vercel.com/docs/functions/runtimes/python
    """
    
    def do_OPTIONS(self):
        """CORS preflight リクエストを処理"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """POSTリクエストを処理"""
        try:
            # Content-Lengthヘッダーを取得
            content_length = int(self.headers.get('Content-Length', 0))
            
            logger.info(f"複数画像処理リクエスト受信: path={self.path}, content_length={content_length}")
            
            if content_length == 0:
                logger.error("リクエストボディが空です")
                self._send_error_response(400, "リクエストボディが空です")
                return
            
            # リクエストボディを読み込み
            body_bytes = self.rfile.read(content_length)
            
            logger.info(f"ボディ読み込み完了: size={len(body_bytes)} bytes")
            
            # JSONをパース
            try:
                body_str = body_bytes.decode('utf-8')
                data = json.loads(body_str)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.error(f"JSON パースエラー: {e}")
                self._send_error_response(400, f"無効なJSON形式: {str(e)}")
                return
            
            logger.info(f"JSON パース成功: keys={list(data.keys())}")
            
            # 複数画像データを取得
            images_data = data.get('images', [])
            mode = data.get('mode', 'vertical')
            upscale_method = data.get('upscale_method', 'simple')
            
            if not images_data:
                logger.error("画像データが空です")
                self._send_error_response(400, "画像データが空です")
                return
            
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
                self._send_error_response(500, f"すべての画像の処理に失敗しました: {', '.join(errors)}")
                return
            
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
            response_data = {
                'success': True,
                'images': processed_images,
                'zip_data': f'data:application/zip;base64,{zip_base64}',
                'zip_filename': 'processed_images.zip',
                'errors': errors if errors else None
            }
            
            self._send_json_response(200, response_data)
            logger.info("レスポンス送信完了")
            
        except Exception as e:
            logger.error(f"予期しないエラー: {type(e).__name__}: {str(e)}", exc_info=True)
            self._send_error_response(500, f"サーバーエラー: {str(e)}")
    
    def do_GET(self):
        """GETリクエストを処理（エラーを返す）"""
        logger.warning(f"GET リクエストを受信: path={self.path}")
        self._send_error_response(405, "Method not allowed. Use POST.")
    
    def _send_json_response(self, status_code: int, data: dict):
        """JSON レスポンスを送信"""
        response_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)
    
    def _send_error_response(self, status_code: int, error_message: str):
        """エラー レスポンスを送信"""
        error_data = {
            'success': False,
            'error': error_message
        }
        self._send_json_response(status_code, error_data)
