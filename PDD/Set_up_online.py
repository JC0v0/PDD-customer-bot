import json
import logging
import requests
from typing import Dict, Any
from config import set_csstatus_url
from utils.logger import get_logger, get_log_queue



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

class AccountMonitor:
    def __init__(self, file_path: str = 'config/account_cookies.json'):
        self.file_path = file_path
        self.accounts = self.load_accounts()
        self.logger = get_logger('set_up_online')
        
    def load_accounts(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"账户文件 {self.file_path} 不存在")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"账户文件 {self.file_path} JSON 格式错误")
            return {}

    @staticmethod
    def set_csstatus(account_name: str, account_data: Dict[str, Any], status: str) -> Dict[str, Any]:
        # 将文本状态转换为数字状态
        if status in STATUS_MAP:
            status = STATUS_MAP[status]
        url = set_csstatus_url
        
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
        
        cookies = account_data['cookies']
        
        try:
            response = requests.post(url, headers=headers, json=data, cookies=cookies)
            
            if response.status_code == 200:
                return {'success': True}
            else:
                return {'success': False}

        except Exception as e:
            return {'success': False, 'error': str(e)}
    def batch_set_csstatus(self, status: str) -> None:
        self.logger.info(f"开始为 {len(self.accounts)} 个账号批量设置状态...")

        for account_name, account_data in self.accounts.items():
            self.set_csstatus(account_name, account_data, status)

        self.logger.info("批量设置状态完成")

def set_csstatus(account_name, account_data, status):
    return AccountMonitor.set_csstatus(account_name, account_data, status)

def batch_set_csstatus(status):
    account_manager = AccountMonitor()
    account_manager.batch_set_csstatus(status)
