from fastapi import FastAPI
from .controllers.message_controller import router as message_router
from .config.settings import settings
from .utils.logger import setup_logging

# 初始化日志
setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="企业微信消息服务",
    description="用于发送企业微信消息的API服务",
    version="1.0.0"
)

# 添加路由
app.include_router(message_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=True
    )
