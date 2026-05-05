import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from backend.database import init_db
from backend.config import AUDIO_DIR, LOG_DIR, BASE_DIR
from backend.routers import synthesize, voices, history, settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(LOG_DIR / "app.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MiMo TTS Studio", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(synthesize.router)
app.include_router(voices.router)
app.include_router(history.router)
app.include_router(settings.router)

app.mount("/api/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")


@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("MiMo TTS Studio 后端服务已启动")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理：捕获所有未处理的异常，返回统一格式的错误响应。"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )


# 生产模式：挂载前端构建产物
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    logger.info(f"已加载前端静态文件: {frontend_dist}")
