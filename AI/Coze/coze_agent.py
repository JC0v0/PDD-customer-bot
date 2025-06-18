from config.config_manager import get_config
from utils.logger import get_logger, get_log_queue
from cozepy import Coze, TokenAuth
from datetime import datetime, timedelta
from utils.conversation import ConversationModel
from utils.database import db, app
import os

class CozeAgent:
    def __init__(self):
        self.logger = get_logger('coze_api')
        self.log_queue = get_log_queue()
        self.expire_days = 180  # 设置过期时间为180天
        self.config_manager = get_config()  # 获取配置管理器实例
        
        # 初始化Coze客户端
        self._initialize_coze()
        
        # 确保数据库文件所在目录存在
        db_path = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        os.makedirs(db_path, exist_ok=True)
        
        # 初始化数据库
        with app.app_context():
            db.create_all()
    
    def _initialize_coze(self):
        """初始化Coze客户端"""
        try:
            coze_token = self.config_manager.coze_token
            if not coze_token:
                self.logger.error("Coze Token 未配置")
                self.coze = None
                return
                
            self.coze = Coze(auth=TokenAuth(token=coze_token), base_url="https://api.coze.cn")
            self.logger.info("Coze客户端初始化成功")
        except Exception as e:
            self.logger.error(f"Coze客户端初始化失败: {e}")
            self.coze = None
    
    def _get_bot_id(self):
        """获取Bot ID"""
        bot_id = self.config_manager.coze_bot_id
        if not bot_id:
            self.logger.error("Coze Bot ID 未配置")
            return None
        return bot_id
    
    def generate_reply(self, recipient_uid, message_content):
        """生成AI回复"""
        # 检查Coze客户端是否初始化成功
        if not self.coze:
            self.logger.error("Coze客户端未初始化，无法生成回复")
            return "AI服务当前不可用，请联系管理员配置"
        
        # 获取Bot ID
        bot_id = self._get_bot_id()
        if not bot_id:
            self.logger.error("Bot ID未配置，无法生成回复")
            return "AI服务配置不完整，请联系管理员"
        
        try:
            with app.app_context():
                # 获取或创建对话ID
                conversation = ConversationModel.query.filter_by(user_id=recipient_uid).first()
                
                # 检查是否存在有效的对话
                if (conversation is None or 
                    conversation.timestamp < datetime.now() - timedelta(days=self.expire_days)):
                    
                    # 创建新的对话ID
                    conversation_id = self.coze.conversations.create()
                    
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
                
                # 创建消息
                message = self.coze.conversations.messages.create(
                    conversation_id=conversation.conversation_id,
                    content=message_content,
                    role="user",
                    content_type="text"
                )

                # 创建聊天并获取回复
                chat = self.coze.chat.create_and_poll(
                    conversation_id=message.conversation_id,
                    bot_id=bot_id,
                    user_id=recipient_uid,
                    additional_messages=[message],
                    auto_save_history=True
                )

                # 提取回复内容
                for message in chat.messages:
                    if message.type.value == 'answer':
                        return message.content
                
                # 如果没有找到回复
                self.logger.warning("未找到AI回复内容")
                return "抱歉，AI暂时无法回复您的问题"
                
        except Exception as e:
            self.logger.error(f"生成AI回复时发生错误: {e}")
            return "AI服务出现错误，请稍后重试"
