from fastapi import APIRouter, HTTPException
from ..models.message_model import WeChatMessageRequest, WeChatMessage
from ..services.message_service import MessageService
import logging

router = APIRouter()
service = MessageService()
logger = logging.getLogger(__name__)


@router.post("/send")
async def send_message(request: WeChatMessageRequest):
    """发送消息接口"""
    try:
        message = WeChatMessage(request.dict())
        return await service.send_message(message)
    except Exception as e:
        logger.error(f"API Error in /send: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-direct")
async def send_direct(message_id: str):
    """直接发送接口(供cron调用)"""
    try:
        message_data = service.get_message(message_id)
        if not message_data:
            raise HTTPException(status_code=404, detail="消息未找到")

        message = WeChatMessage({
            "webhookUrl": message_data["webhook_url"],
            "messageType": message_data["message_type"],
            "messageContent": message_data["message_content"],
            "isScheduled": False
        }, message_id)

        success = await service._send_to_wechat(message)
        if not success:
            raise HTTPException(status_code=500, detail="定时消息发送失败")

        return {"status": "success", "message": "定时消息已发送"}
    except Exception as e:
        logger.error(f"API Error in /send-direct: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}")
async def get_message(message_id: str):
    """获取消息详情"""
    message = service.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="消息未找到")
    return message


@router.delete("/messages/{message_id}")
async def delete_message(message_id: str):
    """删除消息"""
    if not service.delete_message(message_id):
        raise HTTPException(status_code=500, detail="删除消息失败")
    return {"status": "success", "message": "消息已删除"}


@router.get("/messages")
async def list_messages():
    """列出所有消息"""
    return service.list_messages()


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 简单检查数据库连接
        service.list_messages()
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
