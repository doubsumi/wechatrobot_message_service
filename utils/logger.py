import logging
import sys
from pathlib import Path
from ..config.settings import settings


def setup_logging():
    """配置日志系统"""
    log_dir = Path(settings.FILE_STORAGE_PATH).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "wechat_service.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
