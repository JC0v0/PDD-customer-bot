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
from config import LOGIN_URL
import asyncio
from selenium_stealth import stealth
import stat
import shutil
from utils.logger import get_logger,get_log_queue
from selenium.webdriver.common.keys import Keys
import sys


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
        chrome_options.add_argument(f"user-data-dir={os.path.join(self.user_data_dir, account_name)}")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        
        # 获取可执行文件的基础路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的 exe
            base_path = sys._MEIPASS
        else:
            # 如果是开发环境
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 指定ChromeDriver的路径
        chromedriver_path = os.path.join(base_path, "chromedriver-win64", "chromedriver.exe")

        # 检查文件是否存在
        if not os.path.exists(chromedriver_path):
            # 尝试在当前目录查找
            current_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
            alternative_path = os.path.join(current_dir, "chromedriver-win64", "chromedriver.exe")
            
            if os.path.exists(alternative_path):
                chromedriver_path = alternative_path
            else:
                raise FileNotFoundError(f"找不到ChromeDriver，已尝试的路径:\n1. {chromedriver_path}\n2. {alternative_path}")
        
        try:
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            stealth(driver,
                languages=["zh-CN", "zh"],
                vendor="Google Inc.",
                platform="Win64",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            return driver
        except Exception as e:
            self.logger.error(f"创建Chrome驱动时发生错误: {e}")
            raise

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

    async def refresh_account_cookies(self, account_name, password=None, max_retries=3):
        """
        刷新账户的cookies
        
        Args:
            account_name (str): 账户名称
            password (str, optional): 账户密码。如果为None，则从accounts中获取
            max_retries (int): 最大重试次数，默认为3
        """
        self.logger.info(f"尝试刷新账户 {account_name} 的 cookies")

        # 如果没有传入密码，则从accounts中获取
        if password is None:
            password = self.accounts.get(account_name, {}).get('password')
            if not password:
                self.logger.error(f"无法获取账户 {account_name} 的密码")
                return False

        # 确保max_retries是整数
        try:
            max_retries = int(max_retries)
        except (ValueError, TypeError):
            max_retries = 3  # 如果转换失败，使用默认值

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
