import requests
from datetime import datetime, timedelta
from config import COZE_API_URL, coze_token, coze_bot_id
from logger import get_logger
logger = get_logger('coze_api')
class CozeAPIHandler:
    def __init__(self):
        self.chat_history = {}
        self.chat_history_timestamps = {}

    def generate_reply(self, recipient_uid, message_content, message_id, extra_info=None):
        headers = {
            "Authorization": f"Bearer {coze_token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Host": "api.coze.cn",
            "Connection": "keep-alive"
        }

        # 为每个用户维护单独的聊天历史
        if recipient_uid not in self.chat_history:
            self.chat_history[recipient_uid] = []
            self.chat_history_timestamps[recipient_uid] = []

        # 将新消息添加到用户的聊天历史
        self.chat_history[recipient_uid].append({"role": "user", "content": message_content})
        self.chat_history_timestamps[recipient_uid].append(datetime.now())

        # 删除12小时前的聊天记录
        self._clean_old_chat_history(recipient_uid)

        # 构建查询字符串
        query = message_content
        if extra_info:
            query += f", {extra_info}"

        payload = {
            "conversation_id": message_id,
            "bot_id": coze_bot_id,
            "user": recipient_uid,
            "query": query,
            "chat_history": self.chat_history[recipient_uid],
            "stream": False
        }

        try:
            response = requests.post(COZE_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            
            if 'messages' in response_data:
                answer_messages = [msg for msg in response_data['messages'] if msg['type'] == 'answer']
                if answer_messages:
                    reply = answer_messages[0]['content']
                    # 将AI回复添加到用户的聊天历史
                    self.chat_history[recipient_uid].append({"role": "assistant", "content": reply})
                    self.chat_history_timestamps[recipient_uid].append(datetime.now())
                    return reply
                else:
                    return "抱歉，我暂时无法回答您的问题。请稍后再试或联系人工客服。"
            else:
                return "抱歉，我暂时无法回答您的问题。请稍后再试或联系人工客服。"
        
        except Exception as e:
            logger.info(f"调用Coze API时发生错误：{e}")
            return "抱歉，我暂时无法回答您的问题。请稍后再试或联系人工客服。"

    def _clean_old_chat_history(self, recipient_uid):
        current_time = datetime.now()
        while self.chat_history_timestamps[recipient_uid] and (current_time - self.chat_history_timestamps[recipient_uid][0]) > timedelta(hours=12):
            self.chat_history[recipient_uid].pop(0)
            self.chat_history_timestamps[recipient_uid].pop(0)