import subprocess
import re
import os
from typing import List
from ...config.settings import settings
import logging

logger = logging.getLogger(__name__)


class CronManager:
    """Cron任务管理器"""

    @staticmethod
    def add_cron_job(message_id: str, cron_expression: str, command: str):
        """添加cron任务"""
        try:
            if not CronManager._validate_cron_expression(cron_expression):
                raise ValueError("Invalid cron expression")

            clean_command = CronManager._sanitize_command(command)
            cron_line = f"{cron_expression} root {clean_command} # {message_id}\n"

            CronManager.remove_cron_job(message_id)

            with open(settings.CRONTAB_FILE, "a") as f:
                f.write(cron_line)

            subprocess.run(["crontab", settings.CRONTAB_FILE], check=True)
            logger.info(f"Added cron job for message {message_id}")
        except Exception as e:
            logger.error(f"Failed to add cron job: {e}")
            raise

    @staticmethod
    def remove_cron_job(message_id: str):
        """移除cron任务"""
        try:
            if not os.path.exists(settings.CRONTAB_FILE):
                return False

            with open(settings.CRONTAB_FILE, "r") as f:
                lines = f.readlines()

            new_lines = [line for line in lines if f"# {message_id}" not in line]

            if len(new_lines) != len(lines):
                with open(settings.CRONTAB_FILE, "w") as f:
                    f.writelines(new_lines)

                subprocess.run(["crontab", settings.CRONTAB_FILE], check=True)
                logger.info(f"Removed cron job for message {message_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove cron job: {e}")
            return False

    @staticmethod
    def _validate_cron_expression(expression: str) -> bool:
        """验证cron表达式"""
        pattern = r"^(\*|([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])|\*\/([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])) (" \
                  r"\*|([0-9]|1[0-9]|2[0-3])|\*\/([0-9]|1[0-9]|2[0-3])) (\*|([1-9]|1[0-9]|2[0-9]|3[0-1])|\*\/([" \
                  r"1-9]|1[0-9]|2[0-9]|3[0-1])) (\*|([1-9]|1[0-2])|\*\/([1-9]|1[0-2])) (\*|([0-6])|\*\/([0-6]))$"
        return re.match(pattern, expression) is not None

    @staticmethod
    def _sanitize_command(command: str) -> str:
        """命令消毒"""
        return re.sub(r"[;&|`]", "", command).strip()
