import requests
import json
import os
from utils.logger import get_logger, get_log_queue

class GetAccessToken:
    def __init__(self, account_name, headers, cookies,file_path='config/account_cookies.json'):
        self.account_name = account_name
        self.headers = headers
        self.cookies = cookies
        self.file_path = file_path
        self.logger = get_logger('get_access_token')
    def get_access_token(self):
        """
        获取拼多多商家后台聊天token并更新到配置文件
        
        Returns:
            str: 接口返回的token
        """
        # 接口地址
        url = "https://mms.pinduoduo.com/chats/getToken"

        # 请求参数
        payload = {
            'version': '3'
        }

        try:
            # 发送POST请求
            response = requests.post(url, data=payload, headers=self.headers, cookies=self.cookies)
            data = json.loads(response.text)
            token = data.get("token")
            
            if token:
                # 读取现有的配置文件
                config_path = 'config/account_cookies.json'
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 更新指定账号的access_token
                    if self.account_name in config:
                        config[self.account_name]['access_token'] = token
                        
                        # 保存更新后的配置
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=2)
                        
                        self.logger.info(f"成功更新账号 {self.account_name} 的access_token")
                    else:
                        self.logger.error(f"账号 {self.account_name} 不存在于配置文件中")
                
            return token
            
        except Exception as e:
            self.logger.error(f"请求失败: {str(e)}")
            return None

