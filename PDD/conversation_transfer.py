import requests
import random
from config import getAssignCsList_url, move_conversation_url
from logger import get_logger
logger = get_logger('conversation_transfer')
class ConversationTransfer:
    def __init__(self, account_name, headers, cookies):
        self.account_name = account_name
        self.headers = headers
        self.cookies = cookies

    def get_online_cs_list(self):
        data = {"wechatCheck": True}
        try:
            response = requests.post(getAssignCsList_url, headers=self.headers, json=data, cookies=self.cookies)
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    return result['result']['csList']
            return {}
        except Exception as e:
            logger.error(f"获取在线客服列表时发生错误：{e}")
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
            response = requests.post(move_conversation_url, headers=self.headers, json=data, cookies=self.cookies)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"请求失败，状态码：{response.status_code}")
                logger.info("响应内容：", response.text)
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求发生异常：{e}")
            return None

    def auto_transfer_conversation(self, uid):
        online_cs_list = self.get_online_cs_list()
        if not online_cs_list:
            logger.info("没有找到在线客服")
            return None

        selected_cs_id = random.choice(list(online_cs_list.keys()))
        selected_cs = online_cs_list[selected_cs_id]

        result = self.move_conversation(selected_cs_id, uid)
        if result and result.get('success'):
            if result['result'].get('result') == 'ok':
                logger.info(f"成功将用户 {uid} 的对话转移给客服 {selected_cs['username']} (ID: {selected_cs_id})")
            else:
                error_msg = result['result'].get('error_msg', '未知错误')
                logger.error(f"转移对话失败: {error_msg}")
        else:
            logger.error(f"API调用失败")
        
        return result