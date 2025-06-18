import websockets
import json
from utils.logger import get_logger
from PDD.pdd_message import PDDChatMessage
from PDD.get_token import get_token
from PDD.pdd_message import ContextType
from AI.Coze.coze_agent import CozeAgent
from PDD.keyword_transfer import KeywordTransfer
from PDD.conversation_transfer import ConversationTransfer
import requests
import time
logger = get_logger(__name__)

coze_agent = CozeAgent()


class PDDApp:
    def __init__(self, account_name, stop_event=None):
        self.account_name = account_name
        self.stop_event = stop_event  # 添加停止事件
        self.access_token = get_token(account_name)
        self.cookies = json.load(open('config/cookies.json', 'r', encoding='utf-8'))
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json',
        }
        # 已处理的消息ID集合，防止重复回复
        self.processed_messages = set()
        # 不需要回复的消息类型
        self.no_reply_types = {
            ContextType.MALL_CS,  # 商城客服消息（自己发的）
            ContextType.SYSTEM_STATUS,  # 系统状态消息
            ContextType.AUTH,  # 认证消息
            ContextType.MALL_SYSTEM_MSG,  # 商城系统消息
        }
        self.keyword_transfer = KeywordTransfer()
        self.conversation_transfer = ConversationTransfer(self.account_name, self.headers, self.cookies)



    async def start(self):
        # 构建带参数的完整URL
        access_token = get_token(self.account_name)
        params = {
            "access_token": access_token,
            "role": "mall_cs",
            "client": "web",
            "version": "202506091557"
        }
        # 创建查询字符串
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"wss://m-ws.pinduoduo.com/?{query}"
        try:
            async with websockets.connect(
                full_url,
                ping_interval=20,
                ping_timeout=20
            ) as websocket:
                logger.info(f"WebSocket连接成功: {full_url}")
                async for message in websocket:
                    # 检查停止事件
                    if self.stop_event and self.stop_event.is_set():
                        logger.info("检测到停止信号，正在安全退出...")
                        break
                    
                    try:
                        message_data = json.loads(message)
                        
                        data = PDDChatMessage(message_data)
                        
                        # 处理消息
                        await self.handle_message(data)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析错误: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"处理消息时发生错误: {e}")
                        continue
        except Exception as e:
            logger.error(f"连接错误: {str(e)}")
        finally:
            logger.info("WebSocket连接已关闭")


    # 停止账号
    async def stop(self):
        if self.stop_event:
            self.stop_event.set()
        logger.info("账号已停止")


    async def handle_message(self, data):
        """统一的消息处理方法"""
        try:
            # 检查是否需要回复这类消息
            if not self.should_reply(data):
                return
            
            # 防止重复处理同一条消息
            if data.msg_id and data.msg_id in self.processed_messages:
                logger.debug(f"消息 {data.msg_id} 已经处理过，跳过")
                return
            
            # 记录消息ID
            if data.msg_id:
                self.processed_messages.add(data.msg_id)
                # 限制集合大小，防止内存泄漏
                if len(self.processed_messages) > 10000:
                    # 移除最旧的1000条记录
                    old_messages = list(self.processed_messages)[:1000]
                    for old_msg in old_messages:
                        self.processed_messages.discard(old_msg)
            
            # 格式化消息内容
            formatted_content = self.format_message_content(data)
            
            if not formatted_content:
                logger.warning(f"无法格式化消息内容，消息类型: {data.user_msg_type}")
                return
            
            logger.info(f"格式化后的内容: {formatted_content}")
            
            # 关键词自动转接判断
            if self.keyword_transfer.need_human_service(formatted_content):
                logger.info(f"检测到关键词，尝试为用户 {data.from_uid} 转接人工客服")
                # 转人工
                import asyncio
                transfer_result = await asyncio.to_thread(self.conversation_transfer.auto_transfer_conversation, data.from_uid)
                if transfer_result and transfer_result.get('success') and transfer_result['success'].get('result') == 'ok':
                    reply = "您的请求已收到，正在为您转接人工客服，请稍候。"
                else:
                    reply = "抱歉，转接人工客服失败，请稍后再试。"
            else:
                # 生成AI回复
                reply = await self.generate_ai_reply(data.from_uid, formatted_content)

            if reply:
                logger.info(f"AI回复: {reply}")
                # 发送回复
                success = self.send_message(data.from_uid, reply)
                if success:
                    logger.info(f"成功回复用户 {data.from_uid}")
                else:
                    logger.error(f"回复用户 {data.from_uid} 失败")
            else:
                logger.warning(f"系统生成回复失败，用户: {data.from_uid}")
                
        except Exception as e:
            logger.error(f"处理消息时发生异常: {e}")

    def should_reply(self, data):
        """判断是否需要回复这条消息"""
        # 不回复的消息类型
        if data.user_msg_type in self.no_reply_types:
            logger.debug(f"消息类型 {data.user_msg_type} 不需要回复")
            return False
        
        # 不回复自己发送的消息
        if data.from_role == "mall_cs":
            logger.debug("不回复自己发送的消息")
            return False
        
        # 必须有发送者UID
        if not data.from_uid:
            logger.debug("消息没有发送者UID，不回复")
            return False
        
        return True

    def format_message_content(self, data):
        """根据消息类型格式化消息内容"""
        msg_type = data.user_msg_type
        content = data.content
        
        if msg_type == ContextType.TEXT:
            return content
        
        elif msg_type == ContextType.IMAGE:
            return f"用户发送了一张图片: {content}"
        
        elif msg_type == ContextType.VIDEO:
            return f"用户发送了一个视频: {content}"
        
        elif msg_type == ContextType.EMOTION:
            return f"用户发送了表情: {content}"
        
        elif msg_type == ContextType.SYSTEM_TRANSFER:
            return f"收到转接消息: {content}"
        
        elif msg_type == ContextType.GOODS_CARD:
            if isinstance(content, dict):
                return (f"用户查看了商品卡片:\n"
                       f"商品名称: {content.get('goods_name', '未知')}\n"
                       f"商品价格: {content.get('goods_price', '未知')}\n"
                       f"商品链接: {content.get('link_url', '无')}")
            return "用户发送了商品卡片"
        
        elif msg_type == ContextType.GOODS_INQUIRY:
            if isinstance(content, dict):
                return (f"用户商品咨询:\n"
                       f"问题: {content.get('content', '无具体问题')}\n"
                       f"商品名称: {content.get('goods_name', '未知')}\n"
                       f"商品价格: {content.get('goods_price', '未知')}\n"
                       f"商品规格: {content.get('goods_spec', '未知')}")
            return "用户进行了商品咨询"
        
        elif msg_type == ContextType.ORDER_INFO:
            if isinstance(content, dict):
                return (f"用户查询订单信息:\n"
                       f"订单编号: {content.get('order_id', '未知')}\n"
                       f"商品名称: {content.get('goods_name', '未知')}\n")
            return "用户查询了订单信息"
        
        
        else:
            logger.warning(f"未处理的消息类型: {msg_type}")
            return str(content) if content else "收到未知类型消息"

    async def generate_ai_reply(self, user_id, message_content):
        """生成AI回复（异步包装）"""
        try:
            import asyncio
            # 将同步的CozeAgent调用包装成异步
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                coze_agent.generate_reply, 
                user_id, 
                message_content
            )
        except Exception as e:
            logger.error(f"生成AI回复时发生异常: {e}")
            return None

    def send_message(self, recipient_uid, message_content):
        """发送消息给用户"""
        if not recipient_uid or not message_content:
            logger.error("发送消息参数不完整：recipient_uid 或 message_content 为空")
            return False
        
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
                    "content": str(message_content).strip(),
                    "msg_id": None,
                    "type": 0,
                    "is_aut": 0,
                    "manual_reply": 1,
                },
            },
            "client": "WEB"
        }
        
        SEND_MESSAGE_URL = "https://mms.pinduoduo.com/plateau/chat/send_message"
        
        try:
            response = requests.post(
                SEND_MESSAGE_URL, 
                headers=self.headers, 
                json=data, 
                cookies=self.cookies,
                timeout=10  # 添加超时
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"发送消息成功：{result}")
                return True
            else:
                logger.error(f"账号 {self.account_name} 发送消息失败，状态码：{response.status_code}")
                logger.error(f"请求数据：{data}")
                logger.error(f"响应内容：{response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"账号 {self.account_name} 发送消息超时")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"账号 {self.account_name} 发送消息时发生网络异常：{e}")
            return False
        except Exception as e:
            logger.error(f"账号 {self.account_name} 发送消息时发生未知异常：{e}")
            return False


