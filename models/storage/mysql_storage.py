import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from ...config.settings import settings
import logging

logger = logging.getLogger(__name__)


class MySQLStorage:
    """MySQL存储实现"""

    def __init__(self):
        self.config = {
            'host': settings.MYSQL_HOST,
            'port': settings.MYSQL_PORT,
            'user': settings.MYSQL_USER,
            'password': settings.MYSQL_PASSWORD,
            'database': settings.MYSQL_DATABASE
        }
        self._create_connection()
        self._ensure_table_exists()

    def _create_connection(self):
        """创建数据库连接"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor(dictionary=True)
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            raise

    def _ensure_table_exists(self):
        """确保表存在"""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS `wechat_messages` (
                    `id` varchar(64) NOT NULL,
                    `webhook_url` varchar(512) NOT NULL,
                    `message_type` enum('text','markdown','image','news','voice','file') NOT NULL,
                    `message_content` longtext,
                    `is_scheduled` tinyint(1) NOT NULL DEFAULT '0',
                    `cron_expression` varchar(50) DEFAULT NULL,
                    `status` enum('pending','sent','failed') NOT NULL DEFAULT 'pending',
                    `created_at` datetime NOT NULL,
                    `updated_at` datetime DEFAULT NULL,
                    `file_path` varchar(512) DEFAULT NULL,
                    PRIMARY KEY (`id`),
                    KEY `idx_status` (`status`),
                    KEY `idx_created` (`created_at`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            self.connection.commit()
        except Error as e:
            logger.error(f"Error ensuring table exists: {e}")
            raise

    def add_message(self, message: Dict[str, Any]) -> str:
        """添加消息到数据库"""
        try:
            # 处理可能的大文件内容
            file_path = None
            if message['message_type'] in ['image', 'voice', 'file']:
                file_path = self._store_file_content(
                    message['message_id'],
                    message['message_content']
                )
                content_to_store = json.dumps({'file_path': file_path})
            else:
                content_to_store = message['message_content']

            query = """
                INSERT INTO wechat_messages 
                (id, webhook_url, message_type, message_content, is_scheduled, 
                 cron_expression, status, created_at, file_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                message['message_id'],
                message['webhook_url'],
                message['message_type'],
                content_to_store,
                message['is_scheduled'],
                message.get('cron_expression'),
                message.get('status', 'pending'),
                datetime.now(),
                file_path
            )

            self.cursor.execute(query, values)
            self.connection.commit()
            return message['message_id']
        except Error as e:
            self.connection.rollback()
            raise Exception(f"Error adding message: {e}")

    def _store_file_content(self, message_id: str, content: Any) -> str:
        """存储文件内容到本地并返回路径"""
        try:
            # 根据内容类型决定存储方式
            if isinstance(content, dict) and 'base64' in content:
                # Base64编码的文件
                import base64
                file_ext = content.get('type', 'bin')
                file_path = os.path.join(
                    self.file_storage_path,
                    f"{message_id}.{file_ext}"
                )
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(content['base64']))
                return file_path
            elif isinstance(content, str) and content.startswith('data:'):
                # Data URL格式
                import base64
                header, data = content.split(',', 1)
                file_ext = header.split('/')[1].split(';')[0]
                file_path = os.path.join(
                    self.file_storage_path,
                    f"{message_id}.{file_ext}"
                )
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(data))
                return file_path
            else:
                # 其他情况直接存储为JSON
                file_path = os.path.join(
                    self.file_storage_path,
                    f"{message_id}.json"
                )
                with open(file_path, 'w') as f:
                    json.dump(content, f)
                return file_path
        except Exception as e:
            raise Exception(f"Error storing file content: {e}")

    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """获取单个消息"""
        try:
            query = "SELECT * FROM wechat_messages WHERE id = %s"
            self.cursor.execute(query, (message_id,))
            result = self.cursor.fetchone()

            if not result:
                return None

            # 处理文件内容
            if result['file_path'] and os.path.exists(result['file_path']):
                with open(result['file_path'], 'r') as f:
                    if result['file_path'].endswith('.json'):
                        result['message_content'] = json.load(f)
                    else:
                        result['message_content'] = f.read()

            return result
        except Error as e:
            raise Exception(f"Error getting message: {e}")

    def update_message(self, message_id: str, updates: Dict[str, Any]) -> bool:
        """更新消息"""
        try:
            # 构建更新语句
            set_clause = []
            values = []

            for key, value in updates.items():
                set_clause.append(f"{key} = %s")
                values.append(value)

            values.append(message_id)

            query = f"""
                UPDATE wechat_messages 
                SET {', '.join(set_clause)}, updated_at = %s
                WHERE id = %s
            """
            values.append(datetime.now())

            self.cursor.execute(query, values)
            self.connection.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            self.connection.rollback()
            raise Exception(f"Error updating message: {e}")

    def delete_message(self, message_id: str) -> bool:
        """删除消息"""
        try:
            # 先获取消息记录以删除关联文件
            message = self.get_message(message_id)
            if message and message.get('file_path'):
                try:
                    os.remove(message['file_path'])
                except:
                    pass

            # 删除数据库记录
            query = "DELETE FROM wechat_messages WHERE id = %s"
            self.cursor.execute(query, (message_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            self.connection.rollback()
            raise Exception(f"Error deleting message: {e}")

    def get_all_messages(self) -> List[Dict[str, Any]]:
        """获取所有消息(简化版，不加载文件内容)"""
        try:
            query = "SELECT * FROM wechat_messages ORDER BY created_at DESC"
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            raise Exception(f"Error getting all messages: {e}")

    def __del__(self):
        """析构时关闭连接"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'connection'):
            self.connection.close()
