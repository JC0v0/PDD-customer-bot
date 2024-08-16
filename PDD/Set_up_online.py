import json
import logging
import requests
from typing import Dict, Any
from config import set_csstatus_url
from logger import get_logger
logger = get_logger('set_up_online')


STATUS_MAP = {
    "0": "忙碌",
    "1": "在线",
    "3": "离线",
    0: "忙碌",
    1: "在线",
    3: "离线"
}

class AccountMonitor:
    def __init__(self, file_path: str = 'config/account_cookies.json'):
        self.file_path = file_path
        self.accounts = self.load_accounts()

    def load_accounts(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"账户文件 {self.file_path} 不存在")
            return {}
        except json.JSONDecodeError:
            logger.error(f"账户文件 {self.file_path} JSON 格式错误")
            return {}

    @staticmethod
    def set_csstatus(account_name: str, account_data: Dict[str, Any], status: str) -> Dict[str, Any]:
        logger.info(f"设置状态值: {status}")
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
                result = response.json()
                if result.get('success'):
                    status_text = STATUS_MAP.get(status) or STATUS_MAP.get(int(status), "未知状态")
                    logger.info(f"账号 {account_name} 设置状态成功: {status_text}")
                else:
                    logger.error(f"账号 {account_name} 设置状态失败: {result.get('error_msg', '未知错误')}")
                return result
            else:
                logger.error(f"账号 {account_name} 请求失败，状态码：{response.status_code}")
                logger.error(f"响应内容：{response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"账号 {account_name} 请求发生异常：{e}")
            return None
    def batch_set_csstatus(self, status: str) -> None:
        logger.info(f"开始为 {len(self.accounts)} 个账号批量设置状态...")

        for account_name, account_data in self.accounts.items():
            self.set_csstatus(account_name, account_data, status)

        logger.info("批量设置状态完成")

def set_csstatus(account_name, account_data, status):
    return AccountMonitor.set_csstatus(account_name, account_data, status)

def batch_set_csstatus(status):
    account_manager = AccountMonitor()
    account_manager.batch_set_csstatus(status)

if __name__ == "__main__":
    monitor = AccountMonitor()
    monitor.batch_set_csstatus("1")  # 设置所有账号为在线状态