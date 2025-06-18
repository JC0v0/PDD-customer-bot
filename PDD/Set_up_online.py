import json
import requests
from typing import Dict, Any
from utils.logger import get_logger



STATUS_MAP = {
    "0": "忙碌",
    "1": "在线",
    "3": "离线",
    "忙碌":0,
    "在线":1,
    "离线":3,
    0: "忙碌",
    1: "在线",
    3: "离线"
}

class SetUpOnline:
    def __init__(self):
        
        self.logger = get_logger('set_up_online')
        

    def set_csstatus(self, status: str) -> Dict[str, Any]:
        # 将文本状态转换为数字状态
        if status in STATUS_MAP:
            status = STATUS_MAP[status]
        set_csstatus_url='https://mms.pinduoduo.com/plateau/chat/set_csstatus'
        
        data = {
            "data": {
                "cmd": "set_csstatus",
                "status": status
            },
            "client": "WEB"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json',
        }
        cookies = json.load(open('config/cookies.json', 'r', encoding='utf-8'))
        try:
            response = requests.post(set_csstatus_url, headers=headers, json=data, cookies=cookies)
            
            if response.status_code == 200:
                return {'success': True}
            else:
                return {'success': False}

        except Exception as e:
            return {'success': False, 'error': str(e)}


