import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from config import LOGIN_URL
import asyncio
from selenium_stealth import stealth
import stat
from logger import get_logger
logger = get_logger('account_manager')

class AccountManager:
    def __init__(self, file_path='config/account_cookies.json'):
        self.file_path = file_path
        self.accounts = self.load_accounts()

    def load_accounts(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
                for account_name, data in accounts.items():
                    if 'expiry_date' in data:
                        try:
                            expiry_date = datetime.fromisoformat(data['expiry_date'])
                            if expiry_date.tzinfo is None:
                                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                            data['expiry_date'] = expiry_date.isoformat()
                        except ValueError:
                            # 如果日期格式无效，设置一个新的过期时间
                            data['expiry_date'] = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
                return accounts
        return {}

    def save_accounts(self):
        accounts_to_save = {}
        for account_name, data in self.accounts.items():
            account_data = data.copy()
            if 'expiry_date' in account_data:
                if isinstance(account_data['expiry_date'], datetime):
                    account_data['expiry_date'] = account_data['expiry_date'].isoformat()
            accounts_to_save[account_name] = account_data
        
        # 使用绝对路径
        abs_file_path = os.path.abspath(self.file_path)
        temp_dir = os.path.dirname(abs_file_path)
        
        # 确保目录存在
        os.makedirs(temp_dir, exist_ok=True)
        
        # 如果文件存在，尝试更改权限
        if os.path.exists(abs_file_path):
            try:
                os.chmod(abs_file_path, stat.S_IRUSR | stat.S_IWUSR)
            except Exception as e:
                print(f"更改文件权限时出错: {e}")
        
        # 使用临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=temp_dir, encoding='utf-8') as temp_file:
            json.dump(accounts_to_save, temp_file, ensure_ascii=False, indent=2)
            temp_name = temp_file.name
        
        try:
            # 尝试重命名临时文件
            os.replace(temp_name, abs_file_path)
        except OSError as e:
            os.unlink(temp_name)  # 删除临时文件
            logger.error(f"保存账户信息时发生错误: {e}")
            logger.info(f"文件路径: {abs_file_path}")
            logger.info(f"当前工作目录: {os.getcwd()}")
            logger.info(f"文件是否存在: {os.path.exists(abs_file_path)}")
            if os.path.exists(abs_file_path):
                logger.info(f"文件权限: {oct(os.stat(abs_file_path).st_mode)[-3:]}")
            raise
        
        logger.info(f"成功保存账户信息到: {abs_file_path}")

    def get_account_cookies(self, account_name):
        account = self.accounts.get(account_name)
        if account:
            expiry_date = datetime.fromisoformat(account.get('expiry_date', datetime.min.isoformat()))
            if datetime.now(timezone.utc) > expiry_date:
                logger.info(f"账户 {account_name} 的 cookies 已过期，尝试重新登录")
                new_cookies = asyncio.get_event_loop().run_until_complete(self.auto_login(account_name))
                if new_cookies:
                    return new_cookies
                return None
            return account.get('cookies', {})
        logger.info(f"未找到名为 {account_name} 的账户")
        return None

    async def auto_login(self, account_name):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])

        chromedriver_path = "chromedriver-win64/chromedriver.exe"
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        stealth(driver,
            languages=["zh-CN", "zh"],
            vendor="Google Inc.",
            platform="Win64",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        try:
            driver.get(LOGIN_URL)
            logger.info(f"已打开账户 {account_name} 的登录页面")
            
            await asyncio.to_thread(WebDriverWait(driver, 300).until, EC.title_is("拼多多 商家后台"))
            
            cookies = driver.get_cookies()
            new_cookies = {}
            for cookie in cookies:
                if cookie['name'] in ['PASS_ID', 'JSESSIONID']:
                    new_cookies[cookie['name']] = cookie['value']
            
            if len(new_cookies) == 2:
                logger.info(f"账户 {account_name} 登录成功")
                self.accounts[account_name] = {
                    "cookies": new_cookies,
                    "expiry_date": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
                }
                self.save_accounts()
                return new_cookies
            else:
                logger.error(f"账户 {account_name} 登录失败：无法获取所需的 cookies")
                return None
        
        except Exception as e:
            logger.error(f"账户 {account_name} 登录过程中发生错误: {e}")
            return None
        
        finally:
            await asyncio.to_thread(driver.quit)

    async def add_account(self, account_name):
        logger.info(f"尝试添加或更新账户: {account_name}")
        new_cookies = await self.auto_login(account_name)
        
        if new_cookies:
            self.accounts[account_name] = {
                "cookies": new_cookies,
                "expiry_date": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
            }
            self.save_accounts()
            logger.info(f"成功添加或更新账户: {account_name}")
            return True
        else:
            logger.error(f"添加或更新账户失败: {account_name}")
            return False

    async def remove_account(self, account_name):
        if account_name in self.accounts:
            del self.accounts[account_name]
            self.save_accounts()
            logger.info(f"成功移除账户: {account_name}")
            return True
        else:
            logger.error(f"未找到账户 {account_name}。无法移除。")
            return False

    async def batch_add_accounts(self, account_names):
        results = {}
        for account_name in account_names:
            success = await self.add_account(account_name)
            results[account_name] = success
            if success:
                logger.info(f"成功添加或更新账号: {account_name}")
            else:
                logger.error(f"添加或更新账号失败: {account_name}")
        return results