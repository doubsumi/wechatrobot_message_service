from typing import Dict, Any, Optional, List
import requests
from ..models.message_model import WeChatMessage
from ..models.storage.mysql_storage import MySQLStorage
from ..models.storage.cron_manager import CronManager
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)


class MessageService:
    """消息服务"""

    def __init__(self):
        self.storage = MySQLStorage()

    async def send_message(self, message: WeChatMessage) -> Dict[str, Any]:
        """处理消息发送"""
        try:
            # 存储到数据库
            self.storage.add_message(message.to_dict())

            if message.is_scheduled and message.cron_expression:
                # 定时消息
                curl_command = (
                    f"curl -X POST 'http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT}/send-direct' "
                    f"-H 'Content-Type: application/json' "
                    f"-d '{{\"message_id\": \"{message.message_id}\"}}'"
                )

                CronManager.add_cron_job(
                    message_id=message.message_id,
                    cron_expression=message.cron_expression,
                    command=curl_command
                )

                return {
                    "status": "success",
                    "message": "定时消息已安排",
                    "message_id": message.message_id
                }
            else:
                # 立即发送
                success = await self._send_to_wechat(message)
                if success:
                    return {
                        "status": "success",
                        "message": "消息已发送",
                        "message_id": message.message_id
                    }
                raise Exception("消息发送失败")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def _send_to_wechat(self, message: WeChatMessage) -> bool:
        """实际发送到企业微信"""
        payload = {
            "msgtype": message.message_type,
            message.message_type: {
                "content": message.message_content
            }
        }

        if message.message_type == "news":
            try:
                import json
                content = json.loads(message.message_content)
                payload[message.message_type] = content
            except:
                pass

        try:
            response = requests.post(
                message.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            self.storage.update_message(message.message_id, {"status": "sent"})
            return True
        except Exception as e:
            self.storage.update_message(
                message.message_id,
                {"status": f"failed: {str(e)}"}
            )
            logger.error(f"Failed to send to WeChat: {e}")
            return False

    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """获取消息详情"""
        return self.storage.get_message(message_id)

    def delete_message(self, message_id: str) -> bool:
        """删除消息"""
        return self.storage.delete_message(message_id)

    def list_messages(self) -> List[Dict[str, Any]]:
        """列出所有消息"""
        return self.storage.get_all_messages()
