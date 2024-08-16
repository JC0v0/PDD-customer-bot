import threading
import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from PDD.messages import Message
from config import *
import queue
import os
import logging
from PDD.keyword_transfer import KeywordTransfer
from PDD.conversation_transfer import ConversationTransfer
from AI.Coze.coze_api import CozeAPIHandler
from logger import get_logger, get_log_queue

# 获取logger和log_queue
logger = get_logger('app')
log_queue = get_log_queue()

class AccountManager:
    def __init__(self, file_path='config/account_cookies.json'):
        self.file_path = file_path
        self.accounts = self.load_accounts()

    def load_accounts(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

class AccountMonitor:
    def __init__(self, account_name, account_data):
        self.account_name = account_name
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json',
        }
        self.cookies = account_data['cookies']
        self.last_processed_msg_id = None
        self.keyword_transfer = KeywordTransfer()
        self.conversation_transfer = ConversationTransfer(account_name, self.headers, self.cookies)
        self.coze_api_handler = CozeAPIHandler()
        self.chat_log_dir = os.path.join("chat_logs", account_name)
        os.makedirs(self.chat_log_dir, exist_ok=True)

    def get_latest_messages(self):
        data = {"data":{"offset":0,"size":10}}
        try:
            response = requests.post(LATEST_CONVERSATIONS_URL, headers=self.headers, json=data, cookies=self.cookies)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"账号 {self.account_name} 请求发生异常：{e}")
            return None
        
    def save_chat_log(self, user_id, message, is_user=True):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "role": "user" if is_user else "assistant",
            "content": message
        }
        
        chat_log_file = os.path.join(self.chat_log_dir, f"{user_id}_chat_log.json")
        
        try:
            if os.path.exists(chat_log_file):
                with open(chat_log_file, 'r+', encoding='utf-8') as f:
                    chat_log = json.load(f)
                    chat_log.append(log_entry)
                    f.seek(0)
                    json.dump(chat_log, f, ensure_ascii=False, indent=2)
            else:
                with open(chat_log_file, 'w', encoding='utf-8') as f:
                    json.dump([log_entry], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存聊天记录时发生错误: {e}")
            
    def process_new_messages(self, messages):
        processed_messages = []
        for msg_data in messages:
            msg = Message.from_dict(msg_data)
            if not msg.status == 'read':
                message_info = {
                    "账号": self.account_name,
                    "时间": msg.timestamp,
                    "店铺名称": msg.mallName,
                    "发送者": f"{msg.from_user.uid} (角色: {msg.from_user.role})",
                    "接收者": f"{msg.to_user.uid} (角色: {msg.to_user.role})",
                    "内容": msg.content,
                    "消息ID": msg.msg_id,
                    "消息类型": msg.type,
                    "是否自动回复": '是' if msg.is_aut else '否',
                    "是否人工回复": '是' if msg.manual_reply else '否',
                    "消息状态": msg.status,
                    "是否已读": '是' if msg.is_read else '否'
                }
                
                if msg.cs_type is not None:
                    message_info["客服类型"] = msg.cs_type
                if msg.from_user.csid:
                    message_info["客服ID"] = msg.from_user.csid
                
                if msg.is_goods_card():
                    message_info["商品信息"] = {
                        "商品名称": msg.get_goods_name(),
                        "商品价格": msg.get_goods_price(),
                        "销售提示": msg.get_sales_tip(),
                        "商品标签": ', '.join(tag['text'] for tag in msg.get_goods_tags()),
                        "服务标签": ', '.join(msg.get_service_tags()),
                        "商品ID": msg.get_goods_id()
                    }
                
                processed_messages.append(message_info)
        return processed_messages

    def send_customer_service_message(self, recipient_uid, message_content):
        data = {
            "data": {
                "cmd": "send_message",
                "request_id": int(time.time() * 1000),
                "message": {
                    "to": {
                        "role": "user",
                        "uid": recipient_uid
                    },
                    "from": {
                        "role": "mall_cs"
                    },
                    "content": message_content,
                    "msg_id": None,
                    "type": 0,
                    "is_aut": 0,
                    "manual_reply": 1,
                },
            },
            "client": "WEB"
        }

        try:
            response = requests.post(SEND_MESSAGE_URL, headers=self.headers, json=data, cookies=self.cookies)
            if response.status_code == 200:
                logger.info(f"账号 {self.account_name} 成功发送消息给 {recipient_uid}: {message_content}")
                return response.json()
            else:
                logger.error(f"账号 {self.account_name} 发送消息失败，状态码：{response.status_code}")
                logger.error(f"响应内容：{response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"账号 {self.account_name} 发送消息时发生异常：{e}")
            return None

    def auto_reply(self, message):
        content = message['内容']
        recipient_uid = message['发送者'].split()[0]

        # 保存用户消息到聊天记录
        self.save_chat_log(recipient_uid, content, is_user=True)

        if self.keyword_transfer.need_human_service(content):
            transfer_result = self.conversation_transfer.auto_transfer_conversation(recipient_uid)
            reply = "您的请求已收到，正在为您转接人工客服，请稍候。" if transfer_result and transfer_result.get('success') else "抱歉，转接人工客服失败，请稍后再试。"
        else:
            extra_info = None
            if message.get('商品信息'):
                extra_info = f"商品信息: {message['商品信息']}"
            reply = self.coze_api_handler.generate_reply(recipient_uid, content, message['消息ID'], extra_info)

        # 保存系统回复到聊天记录
        self.save_chat_log(recipient_uid, reply, is_user=False)
        return reply
            
    def monitor_and_reply(self, stop_event):
        logger.info(f"开始监控账号 {self.account_name} 的未读消息并自动回复...")
        while not stop_event.is_set():
            try:
                response = self.get_latest_messages()
                if response and response.get('success'):
                    conversations = response.get('result', {}).get('conversations', [])
                    if conversations:
                        new_messages = [msg for msg in conversations if msg.get('msg_id') != self.last_processed_msg_id]
                        if new_messages:
                            processed_messages = self.process_new_messages(new_messages)
                            self.last_processed_msg_id = new_messages[0].get('msg_id')
                            for message in processed_messages:
                                logger.info(f"\n账号 {self.account_name} 收到新消息：")
                                logger.info(json.dumps(message, ensure_ascii=False, indent=2, default=str))

                                # 自动回复
                                reply_content = self.auto_reply(message)
                                recipient_uid = message['发送者'].split()[0]  # 提取UID
                                self.send_customer_service_message(recipient_uid, reply_content)
                        else:
                            logger.info(f"{datetime.now()}: 账号 {self.account_name} 没有新的未读消息")
                    else:
                        logger.info(f"{datetime.now()}: 账号 {self.account_name} 没有对话")
                else:
                    logger.warning(f"{datetime.now()}: 账号 {self.account_name} 获取消息失败")
            except Exception as e:
                logger.error(f"{datetime.now()}: 账号 {self.account_name} 处理消息时发生错误: {e}")
            
            # 检查是否收到停止信号
            if stop_event.is_set():
                break
            time.sleep(3)  # 每3秒检查一次
        
        logger.info(f"账号 {self.account_name} 的监控已停止")

def monitor_all_accounts(stop_event):
    account_manager = AccountManager()
    accounts = account_manager.accounts

    logger.info(f"开始监控 {len(accounts)} 个账号...")

    with ThreadPoolExecutor(max_workers=len(accounts)) as executor:
        futures = [executor.submit(AccountMonitor(account_name, account_data).monitor_and_reply, stop_event) 
                for account_name, account_data in accounts.items()]
        
        while not stop_event.is_set():
            if all(future.done() for future in futures):
                break
            time.sleep(1)

        if stop_event.is_set():
            logger.info("收到停止信号，正在停止所有监控...")
            for future in futures:
                if not future.done():
                    future.cancel()
    
    logger.info("所有账号监控已停止")

if __name__ == "__main__":
    stop_event = threading.Event()
    try:
        monitor_all_accounts(stop_event)
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断。正在停止所有监控...")
        stop_event.set()
    except Exception as e:
        logger.error(f"{datetime.now()}: 发生错误: {e}")
        logger.info("5秒后重新启动监控...")
        time.sleep(5)
        stop_event.clear()
        monitor_all_accounts(stop_event)