from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import image
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="画像リサイズ高解像度化API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(image.router, prefix="/api", tags=["image"])

@app.get("/")
async def root():
    return {"message": "画像リサイズ高解像度化API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

