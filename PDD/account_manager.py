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
import shutil
from utils.logger import get_logger,get_log_queue
from selenium.webdriver.common.keys import Keys


class AccountManager:
    def __init__(self, file_path='config/account_cookies.json'):
        self.file_path = file_path
        self.user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
        self.logger = get_logger('account_manager')
        self.log_queue = get_log_queue()
        self.accounts = self.load_accounts()
    def load_accounts(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
            self.logger.info(f"成功加载了 {len(accounts)} 个账号")
            for account_name, data in accounts.items():
                data['expiry_date'] = self.parse_expiry_date(data.get('expiry_date'))
            return accounts
        except FileNotFoundError:
            self.logger.error(f"账号配置文件 {self.file_path} 不存在")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"账号配置文件 {self.file_path} 格式错误")
            return {}

    def parse_expiry_date(self, expiry_date_str):
        if expiry_date_str:
            try:
                expiry_date = datetime.fromisoformat(expiry_date_str)
                if expiry_date.tzinfo is None:
                    expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                return expiry_date.isoformat()
            except ValueError:
                return (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        return (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()

    def get_accounts(self):
        return list(self.accounts.keys())

    def save_accounts(self):
        """
        保存账户信息。
        
        此函数的目的是将当前所有的账户信息进行处理并保存到文件中。
        它遍历每个账户，将账户信息转换为适合存储的格式，特别是对‘expiry_date’
        字段进行处理，确保其为ISO格式的字符串，以便可以正确地写入文件。
        """
        # 初始化一个空字典，用于存储即将保存的账户信息
        accounts_to_save = {}
        
        # 遍历当前所有账户及其对应的数据
        for account_name, data in self.accounts.items():
            # 复制当前账户的数据，避免修改原始数据
            account_data = data.copy()
            
            # 检查账户数据中是否包含‘expiry_date’字段
            if 'expiry_date' in account_data:
                # 如果‘expiry_date’存在，并且其类型为datetime对象
                if isinstance(account_data['expiry_date'], datetime):
                    # 将其转换为ISO格式的字符串
                    account_data['expiry_date'] = account_data['expiry_date'].isoformat()
            
            # 将处理后的账户数据添加到待保存的字典中
            accounts_to_save[account_name] = account_data
        
        # 将所有处理后的账户数据写入文件
        self.write_to_file(accounts_to_save)

    def write_to_file(self, data):
        abs_file_path = os.path.abspath(self.file_path)
        temp_dir = os.path.dirname(abs_file_path)
        
        os.makedirs(temp_dir, exist_ok=True)
        
        if os.path.exists(abs_file_path):
            try:
                os.chmod(abs_file_path, stat.S_IRUSR | stat.S_IWUSR)
            except Exception as e:
                self.logger.error(f"更改文件权限时出错: {e}")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=temp_dir, encoding='utf-8') as temp_file:
            json.dump(data, temp_file, ensure_ascii=False, indent=2)
            temp_name = temp_file.name
        
        try:
            os.replace(temp_name, abs_file_path)
        except OSError as e:
            os.unlink(temp_name)
            self.logger.error(f"保存账户信息时发生错误: {e}")
            if os.path.exists(abs_file_path):
                self.logger.info(f"文件权限: {oct(os.stat(abs_file_path).st_mode)[-3:]}")
            raise
        
    def get_account_cookies(self, account_name):
        account = self.accounts.get(account_name)
        if account:
            if self.is_expired(account.get('expiry_date')):
                self.logger.info(f"账户 {account_name} 的 cookies 已过期，尝试刷新")
                success = asyncio.get_event_loop().run_until_complete(self.refresh_account_cookies(account_name))
                if success:
                    return self.accounts[account_name].get('cookies', {})
                return None
            return account.get('cookies', {})
        self.logger.info(f"未找到名为 {account_name} 的账户")
        return None

    def is_expired(self, expiry_date_str):
        if not expiry_date_str:
            return True
        expiry_date = datetime.fromisoformat(expiry_date_str)
        return datetime.now(timezone.utc) > expiry_date

    async def auto_login(self, account_name, password):
        driver = self.get_driver(account_name)
        try:
            driver.get(LOGIN_URL)
            
            # 点击"账号登录"按钮
            try:
                account_login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '账号登录')]"))
                )
                account_login_button.click()
            except Exception as e:
                self.logger.error(f"点击'账号登录'元素时出错: {e}")

            # 输入用户名（账号名称）
            try:
                username_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "usernameId"))
                )
                username_input.clear()  # 清除可能存在的默认值
                username_input.send_keys(account_name)
            except Exception as e:
                self.logger.error(f"输入用户名时出错: {e}")

            # 输入密码
            try:
                password_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "passwordId"))
                )
                password_input.clear()  # 清除可能存在的默认值
                password_input.send_keys(password)
            except Exception as e:
                self.logger.error(f"输入密码时出错: {e}")

            # 点击登录按钮
            try:
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@class='BTN_outerWrapper_5-95-0 BTN_danger_5-95-0 BTN_large_5-95-0 BTN_outerWrapperBtn_5-95-0']//span[text()='登录']"))
                )
                login_button.click()
            except Exception as e:
                self.logger.error(f"点击登录按钮时出错: {e}")

            # 等待登录完成
            WebDriverWait(driver, 300).until(EC.title_is("拼多多 商家后台"))
            
            # 获取新的 cookies
            new_cookies = extract_cookies(driver)
            if len(new_cookies) == 2:
                self.logger.info(f"账户 {account_name} 登录成功")
                self.accounts[account_name] = {
                    "cookies": new_cookies,
                    "expiry_date": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
                }
                self.save_accounts()
                return new_cookies
            else:
                self.logger.error(f"账户 {account_name} 登录失败：无法获取所需的 cookies")
                return None
        
        except Exception as e:
            self.logger.error(f"账户 {account_name} 登录过程中发生错误: {e}")
            return None
        finally:
            driver.quit()

    def get_driver(self, account_name):
        """
        获取一个配置好的Chrome浏览器驱动。

        :param account_name: 账号名称，用于指定用户数据目录
        :return: 配置好的Chrome浏览器驱动
        """
        # 创建Chrome浏览器选项
        chrome_options = Options()
        # 设置用户数据目录，以便每个账号有独立的浏览器配置
        chrome_options.add_argument(f"user-data-dir={os.path.join(self.user_data_dir, account_name)}")
        # 最大化窗口
        chrome_options.add_argument("--start-maximized")
        # 禁用扩展
        chrome_options.add_argument("--disable-extensions")
        # 排除自动化控制的提示
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        
        # 指定ChromeDriver的路径
        chromedriver_path = "chromedriver-win64/chromedriver.exe"
        # 创建ChromeDriver服务
        service = Service(chromedriver_path)
        # 创建Chrome浏览器驱动
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 使用stealth库来伪装浏览器，避免被检测为自动化工具
        stealth(driver,
            languages=["zh-CN", "zh"],  # 设置语言
            vendor="Google Inc.",  # 设置浏览器厂商
            platform="Win64",  # 设置平台
            webgl_vendor="Intel Inc.",  # 设置WebGL厂商
            renderer="Intel Iris OpenGL Engine",  # 设置渲染器
            fix_hairline=True,  # 修复细线问题
        )
        return driver

    async def get_or_create_browser(self, account_name):
        return self.get_driver(account_name)

    async def close_all_browsers(self):
        # 这个方法可以保留为空，因为我们不再需要主动关闭浏览器
        pass

    async def add_account(self, account_name, password):
        new_cookies = await self.auto_login(account_name, password)
        
        if new_cookies:
            self.accounts[account_name] = {
                "password": password,
                "cookies": new_cookies,
                "expiry_date": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
            }
            self.save_accounts()
            self.logger.info(f"成功添加或更新账户: {account_name}")
            return True
        else:
            self.logger.error(f"添加或更新账号失败: {account_name}")
            return False

    async def remove_account(self, account_name):
        if account_name in self.accounts:
            del self.accounts[account_name]
            self.save_accounts()
            self.delete_account_file(account_name)
            return True
        else:
            self.logger.warning(f"尝试删除不存在的账号: {account_name}")
            return False

    async def batch_add_accounts(self, accounts_info):
        results = {}
        for account_name, password in accounts_info.items():
            success = await self.add_account(account_name, password)
            results[account_name] = success
            if success:
                self.logger.info(f"成功添加或更新账号: {account_name}")
            else:
                self.logger.error(f"添加或更新账号失败: {account_name}")
        return results

    async def refresh_account_cookies(self, account_name, password, max_retries=3):
        self.logger.info(f"尝试刷新账户 {account_name} 的 cookies")
        
        for attempt in range(max_retries):
            new_cookies = await self.auto_login(account_name, password)
            if new_cookies:
                self.accounts[account_name] = {
                    "password": password,
                    "cookies": new_cookies,
                    "expiry_date": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
                }
                self.save_accounts()
                self.logger.info(f"成功刷新账户 {account_name} 的 cookies")
                return True
            else:
                self.logger.warning(f"刷新账户 {account_name} 的 cookies 失败，尝试次数：{attempt + 1}")
        
        self.logger.error(f"刷新账户 {account_name} 的 cookies 失败，已达到最大重试次数")
        return False

    def delete_account_file(self, account_name):
        account_folder_path = os.path.join(self.user_data_dir, account_name)
        if os.path.exists(account_folder_path):
            try:
                shutil.rmtree(account_folder_path, ignore_errors=True)
            except Exception as e:
                self.logger.error(f"删除账户文件夹时发生错误: {e}")
                try:
                    os.system(f'rmdir /S /Q "{account_folder_path}"')
                except Exception as e:
                    self.logger.error(f"使用系统命令删除账户文件夹时发生错误: {e}")
        else:
            self.logger.debug(f"账户文件夹不存在: {account_folder_path}")

    def update_account_password(self, username, new_password):
        for account in self.accounts:
            if account['username'] == username:
                account['password'] = new_password
                self.save_accounts()  # 假设有一个保存账户信息的方法
                return True
        return False

    async def edit_account(self, old_account_name, new_account_name, new_password):
        if old_account_name not in self.accounts:
            return False

        # 如果新旧账号名不同，需要删除旧账号并添加新账号，同时更新 Chrome 用户数据目录
        if old_account_name != new_account_name:
            account_data = self.accounts[old_account_name]
            del self.accounts[old_account_name]
            self.accounts[new_account_name] = account_data

            # 更新 Chrome 用户数据目录
            old_user_data_dir = os.path.join(self.user_data_dir, old_account_name)
            new_user_data_dir = os.path.join(self.user_data_dir, new_account_name)
            if os.path.exists(old_user_data_dir):
                try:
                    shutil.move(old_user_data_dir, new_user_data_dir)
                    self.logger.info(f"成功更新 Chrome 用户数据目录: {old_account_name} -> {new_account_name}")
                except Exception as e:
                    self.logger.error(f"更新 Chrome 用户数据目录时发生错误: {e}")
                    return False

        # 更新密码
        self.accounts[new_account_name]['password'] = new_password

        # 重新获取 cookies
        success = await self.refresh_account_cookies(new_account_name, new_password)
        if not success:
            return False

        # 保存更改到文件
        self.save_accounts()
        return True

def extract_cookies(driver):
    """从 Selenium 驱动中提取 cookies 并返回字典"""
    cookies = driver.get_cookies()
    return {cookie['name']: cookie['value'] for cookie in cookies if cookie['name'] in ['PASS_ID', 'JSESSIONID']}
