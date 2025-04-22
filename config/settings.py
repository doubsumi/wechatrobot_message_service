import os
from pathlib import Path


class Settings:
    # MySQL配置
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "wechat_user")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "secure_password")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "wechat_message_db")

    # 文件存储配置
    FILE_STORAGE_PATH = os.getenv("FILE_STORAGE_PATH", str(Path(__file__).parent.parent / "storage_files"))
    os.makedirs(FILE_STORAGE_PATH, exist_ok=True)

    # 服务配置
    SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", 12001))

    # Cron配置
    CRONTAB_FILE = os.getenv("CRONTAB_FILE", "/etc/cron.d/wechat_messages")


settings = Settings()
