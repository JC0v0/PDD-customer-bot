import requests
import random
import time
from config.config_manager import get_config
from utils.logger import get_logger, get_log_queue

class ConversationTransfer:
    def __init__(self, account_name, headers, cookies):
        self.account_name = account_name
        self.headers = headers
        self.cookies = cookies
        self.logger = get_logger('conversation_transfer')
        self.config_manager = get_config()  # 获取配置管理器实例
        
    def get_online_cs_list(self):
        data = {"wechatCheck": True}
        try:
            getAssignCsList_url = self.config_manager.getAssignCsList_url
            response = requests.post(getAssignCsList_url, headers=self.headers, json=data, cookies=self.cookies)
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    return result['result']['csList']
            return {}
        except Exception as e:
            self.logger.error(f"获取在线客服列表时发生错误：{e}")
            return {}

    def move_conversation(self, csid, uid, remark="无原因直接转移", need_wx=False):
        data = {
            "data": {
                "cmd": "move_conversation",
                "conversation": {
                    "csid": csid,
                    "uid": uid,
                    "need_wx": need_wx,
                    "remark": remark
                },
            },
            "client": "WEB"
        }
        try:
            move_conversation_url = self.config_manager.move_conversation_url
            response = requests.post(move_conversation_url, headers=self.headers, json=data, cookies=self.cookies)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"请求失败，状态码：{response.status_code}")
                self.logger.info("响应内容：", response.text)
                return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求发生异常：{e}")
            return None

    def auto_transfer_conversation(self, uid):
        online_cs_list = self.get_online_cs_list()
        if not online_cs_list:
            self.logger.info("没有找到在线客服")
            return None

        selected_cs_id = random.choice(list(online_cs_list.keys()))
        selected_cs = online_cs_list[selected_cs_id]

        transfer_success = False
        retry_count = 5

        for attempt in range(retry_count):
            result = self.move_conversation(selected_cs_id, uid)
            if result and result.get('success'):
                if result['success'].get('result') == 'ok':
                    self.logger.info(f"成功将用户 {uid} 的对话转移给客服 {selected_cs['username']} (ID: {selected_cs_id})")
                    transfer_success = True
                    break
                else:
                    error_msg = result['result'].get('error_msg', '未知错误')
                    self.logger.error(f"转移对话失败: {error_msg}")
            else:
                self.logger.error(f"API调用失败，尝试次数: {attempt + 1}")
            
            if attempt < retry_count - 1:
                time.sleep(1)  # 在重试之前等待1秒

        if not transfer_success:
            self.logger.error(f"转移对话失败，已尝试 {retry_count} 次")
        
        return result