from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class WeChatMessageRequest(BaseModel):
    """前端请求数据模型"""
    webhookUrl: str
    messageType: str
    isScheduled: bool
    messageContent: str
    cronExpression: Optional[str] = None


class WeChatMessage:
    """消息业务模型"""

    def __init__(self, data: Dict[str, Any], message_id: Optional[str] = None):
        self.message_id = message_id or self._generate_message_id()
        self.webhook_url = data["webhookUrl"]
        self.message_type = data["messageType"]
        self.message_content = data["messageContent"]
        self.is_scheduled = data["isScheduled"]
        self.cron_expression = data.get("cronExpression")
        self.status = "pending"

    def _generate_message_id(self) -> str:
        """生成消息ID"""
        return datetime.now().strftime("%Y%m%d%H%M%S%f")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message_id": self.message_id,
            "webhook_url": self.webhook_url,
            "message_type": self.message_type,
            "message_content": self.message_content,
            "is_scheduled": 1 if self.is_scheduled else 0,
            "cron_expression": self.cron_expression,
            "status": self.status
        }
