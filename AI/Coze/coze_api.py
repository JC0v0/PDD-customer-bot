from config import COZE_API_URL, coze_token, coze_bot_id
from utils.logger import get_logger, get_log_queue
from cozepy import Coze, TokenAuth
from datetime import datetime, timedelta
from utils.conversation import ConversationModel
from utils.database import db, app
import os

coze = Coze(auth=TokenAuth(token=coze_token),base_url=COZE_API_URL)

class CozeAPIHandler:
    def __init__(self):
        self.logger = get_logger('coze_api')
        self.log_queue = get_log_queue()
        self.expire_days = 180  # 设置过期时间为180天
        
        # 确保数据库文件所在目录存在
        db_path = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        os.makedirs(db_path, exist_ok=True)
        
        # 初始化数据库
        with app.app_context():
            db.create_all()
    
    def generate_reply(self, recipient_uid, message_content, message_id, extra_info=None):
        with app.app_context():
            # 获取或创建对话ID
            conversation = ConversationModel.query.filter_by(user_id=recipient_uid).first()
            
            # 检查是否存在有效的对话
            if (conversation is None or 
                conversation.timestamp < datetime.now() - timedelta(days=self.expire_days)):
                
                # 创建新的对话ID
                conversation_id = coze.conversations.create()
                
                if conversation is None:
                    # 新用户，创建新记录
                    conversation = ConversationModel(
                        user_id=recipient_uid,
                        conversation_id=conversation_id.id
                    )
                    db.session.add(conversation)
                else:
                    # 更新已过期的记录
                    conversation.conversation_id = conversation_id.id
                    conversation.timestamp = datetime.now()
                
                db.session.commit()
                self.logger.info(f"新用户或对话已过期，创建对话ID: {conversation_id.id}")
            else:
                # 更新时间戳
                conversation.timestamp = datetime.now()
                db.session.commit()
            message = coze.conversations.messages.create(
                conversation_id=conversation.conversation_id,
                content=message_content,
                role="user",
                content_type="text"
            )

            chat = coze.chat.create_and_poll(
                conversation_id=message.conversation_id,
                bot_id=coze_bot_id,
                user_id=recipient_uid,
                additional_messages=[message],
                auto_save_history=True
            )

            for message in chat.messages:
                if message.type.value == 'answer':
                    return message.content
