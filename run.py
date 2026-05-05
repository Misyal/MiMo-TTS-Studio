"""开发入口：启动 FastAPI 后端服务（带热重载）"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=18700, reload=True)
