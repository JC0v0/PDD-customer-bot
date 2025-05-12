import os
import json
import tempfile
from datetime import datetime, timedelta, timezone
import asyncio
import stat
import shutil
from utils.logger import get_logger
from queue import Queue
import concurrent.futures
from playwright.async_api import async_playwright
from config import LOGIN_URL

class AccountManager:
    def __init__(self, file_path='config/account_cookies.json'):
        self.file_path = file_path
        self.user_data_dir = os.path.join(os.getcwd(), "browser_user_data")
        self.logger = get_logger('account_manager')
        self.accounts = self.load_accounts()
        self.refresh_processes = {}
        self.refresh_callbacks = {}  # 添加回调函数字典
        self.browsers = {}  # 存储已创建的浏览器实例

    def load_accounts(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
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
        它遍历每个账户，将账户信息转换为适合存储的格式，特别是对'expiry_date'
        字段进行处理，确保其为ISO格式的字符串，以便可以正确地写入文件。
        """
        # 初始化一个空字典，用于存储即将保存的账户信息
        accounts_to_save = {}
        
        # 遍历当前所有账户及其对应的数据
        for account_name, data in self.accounts.items():
            # 复制当前账户的数据，避免修改原始数据
            account_data = data.copy()
            
            # 检查账户数据中是否包含'expiry_date'字段
            if 'expiry_date' in account_data:
                # 如果'expiry_date'存在，并且其类型为datetime对象
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
        """
        使用 Playwright 自动登录并获取 cookies
        
        Args:
            account_name: 账号名称
            password: 账号密码
            
        Returns:
            dict: 包含 cookies 的字典，登录失败则返回 None
        """
        self.logger.info(f"开始为账号 {account_name} 自动登录")
        
        # 创建账号存储目录
        storage_dir = os.path.join(os.getcwd(), "browser_storage")
        os.makedirs(storage_dir, exist_ok=True)
        
        # 账号状态文件路径
        storage_file = os.path.join(storage_dir, f"{account_name}_state.json")
        
        async with async_playwright() as p:
            try:
                # 分离浏览器启动参数和上下文参数
                browser_args = {
                    "headless": False,  # 设置为 True 可以隐藏浏览器界面
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--disable-web-security",
                        "--disable-site-isolation-trials"
                    ]
                }
                
                context_args = {
                    "viewport": {"width": 1920, "height": 1080},
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    "locale": "zh-CN",
                    "timezone_id": "Asia/Shanghai",
                    "device_scale_factor": 1,
                    "is_mobile": False,
                    "has_touch": False,
                    "ignore_https_errors": True,
                }
                
                # 检查是否有保存的登录状态
                if os.path.exists(storage_file):
                    self.logger.info(f"发现账号 {account_name} 已保存的登录状态，尝试使用")
                    try:
                        # 启动浏览器
                        browser = await p.chromium.launch(**browser_args)
                        
                        # 加载已保存的状态
                        with open(storage_file, "r", encoding="utf-8") as f:
                            storage_state = json.load(f)
                        
                        # 使用已保存的状态创建浏览器上下文
                        context = await browser.new_context(storage_state=storage_state, **context_args)
                        page = await context.new_page()
                        
                        # 添加 stealth 脚本
                        await self._add_stealth_script(page)
                        
                        # 尝试访问首页，检查登录状态是否有效
                        await page.goto(LOGIN_URL)
                        
                        # 等待一小段时间，让页面加载
                        await page.wait_for_timeout(3000)
                        
                        # 检查是否已登录（通过URL判断）
                        current_url = page.url
                        if "/home" in current_url:
                            self.logger.info(f"账号 {account_name} 已登录状态有效")
                            
                            # 获取 cookies
                            cookies = await context.cookies()
                            all_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                            
                            if 'PASS_ID' in all_cookies:
                                self.logger.info(f"账户 {account_name} 使用已保存状态登录成功")
                                self.accounts[account_name] = {
                                    "password": password,
                                    "cookies": all_cookies,
                                    "expiry_date": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
                                }
                                self.save_accounts()
                                await context.close()
                                await browser.close()
                                return all_cookies
                        
                        self.logger.info(f"账号 {account_name} 已保存状态已失效，需要重新登录")
                        await context.close()
                        await browser.close()
                    except Exception as e:
                        self.logger.error(f"使用已保存状态时出错: {e}")
                
                # 如果没有保存的状态或状态无效，执行正常登录流程
                self.logger.info(f"开始为账号 {account_name} 执行登录流程")
                
                # 启动浏览器
                browser = await p.chromium.launch(**browser_args)
                context = await browser.new_context(**context_args)
                page = await context.new_page()
                
                # 添加 stealth 脚本
                await self._add_stealth_script(page)
                
                # 导航到登录页面
                await page.goto(LOGIN_URL)
                
                # 点击"账号登录"按钮
                try:
                    await page.click("text=账号登录", timeout=10000)
                except Exception as e:
                    self.logger.error(f"点击'账号登录'元素时出错: {e}")
                
                # 输入用户名
                try:
                    await page.fill("#usernameId", account_name, timeout=10000)
                except Exception as e:
                    self.logger.error(f"输入用户名时出错: {e}")
                
                # 输入密码
                try:
                    await page.fill("#passwordId", password, timeout=10000)
                except Exception as e:
                    self.logger.error(f"输入密码时出错: {e}")
                
                # 点击登录按钮
                try:
                    await page.click("button:has-text('登录')", timeout=10000)
                except Exception as e:
                    self.logger.error(f"点击登录按钮时出错: {e}")
                
                # 等待登录完成
                await page.wait_for_url("**/home**", timeout=300000)
                
                # 保存登录状态
                storage_state = await context.storage_state()
                with open(storage_file, "w", encoding="utf-8") as f:
                    json.dump(storage_state, f, ensure_ascii=False, indent=2)
                self.logger.info(f"已保存账号 {account_name} 的登录状态")
                
                # 获取 cookies
                cookies = await context.cookies()
                self.logger.debug(f"获取到的 cookies: {cookies}")
                
                # 提取所有 cookies 到字典
                all_cookies = {}
                for cookie in cookies:
                    all_cookies[cookie['name']] = cookie['value']
                
                # 检查是否包含 PASS_ID，这是必需的
                if 'PASS_ID' in all_cookies:
                    self.logger.info(f"账户 {account_name} 登录成功")
                    self.accounts[account_name] = {
                        "password": password,
                        "cookies": all_cookies,  # 保存所有 cookies
                        "expiry_date": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
                    }
                    self.save_accounts()
                    await context.close()
                    await browser.close()
                    return all_cookies
                else:
                    self.logger.error(f"账户 {account_name} 登录失败：无法获取所需的 cookies (PASS_ID)")
                    await context.close()
                    await browser.close()
                    return None
                
            except Exception as e:
                self.logger.error(f"账户 {account_name} 登录过程中发生错误: {e}")
                return None

    async def _add_stealth_script(self, page):
        """添加 stealth 脚本到页面"""
        await page.add_init_script("""
        // 覆盖 WebDriver 属性
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        // 覆盖 Chrome 属性
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {},
        };
        
        // 覆盖 Permissions 属性
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
        
        // 添加语言和平台信息
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en'],
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: 'application/pdf'},
                    description: 'Portable Document Format',
                    filename: 'internal-pdf-viewer',
                    length: 1,
                    name: 'Chrome PDF Plugin'
                }
            ],
        });
        """)

    async def get_driver(self, account_name):
        """
        获取或创建一个与账号关联的浏览器实例
        
        Args:
            account_name: 账号名称
            
        Returns:
            browser: Playwright 浏览器实例
        """
        if account_name in self.browsers and self.browsers[account_name]['browser']:
            return self.browsers[account_name]['browser']
        
        user_data_dir = os.path.join(self.user_data_dir, account_name)
        os.makedirs(user_data_dir, exist_ok=True)
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
        )
        
        self.browsers[account_name] = {
            'browser': browser,
            'playwright': playwright
        }
        
        return browser

    async def close_browser(self, account_name):
        """关闭指定账号的浏览器实例"""
        if account_name in self.browsers:
            if self.browsers[account_name]['browser']:
                await self.browsers[account_name]['browser'].close()
            if self.browsers[account_name]['playwright']:
                await self.browsers[account_name]['playwright'].stop()
            del self.browsers[account_name]

    async def close_all_browsers(self):
        """关闭所有浏览器实例"""
        for account_name in list(self.browsers.keys()):
            await self.close_browser(account_name)

    async def add_account(self, account_name, password):
        """
        添加新账号或更新现有账号
        
        Args:
            account_name: 账号名称
            password: 账号密码
            
        Returns:
            bool: 操作是否成功
        """
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
        """
        删除账号
        
        Args:
            account_name: 要删除的账号名称
            
        Returns:
            bool: 操作是否成功
        """
        if account_name in self.accounts:
            # 关闭该账号的浏览器实例
            await self.close_browser(account_name)
            
            # 从账号列表中删除
            del self.accounts[account_name]
            self.save_accounts()
            
            # 删除用户数据目录
            self.delete_account_file(account_name)
            return True
        else:
            self.logger.warning(f"尝试删除不存在的账号: {account_name}")
            return False

    async def batch_add_accounts(self, accounts_info):
        """
        批量添加账号
        
        Args:
            accounts_info: 包含账号和密码的字典 {account_name: password}
            
        Returns:
            dict: 包含每个账号添加结果的字典
        """
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
            
        Returns:
            bool: 刷新是否成功
        """
        success = False
        try:
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

            # 关闭现有的浏览器实例
            await self.close_browser(account_name)

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
                    success = True
                    break
                else:
                    self.logger.warning(f"刷新账户 {account_name} 的 cookies 失败，尝试次数：{attempt + 1}")
            
            if not success:
                self.logger.error(f"刷新账户 {account_name} 的 cookies 失败，已达到最大重试次数")
            return success
        finally:
            if account_name in self.refresh_callbacks:
                callback = self.refresh_callbacks.pop(account_name)
                callback(success)

    def is_refreshing(self, username):
        """检查账号是否正在刷新中"""
        return username in self.refresh_processes

    def delete_account_file(self, account_name):
        """删除账号的状态文件"""
        # 删除浏览器存储状态文件
        storage_dir = os.path.join(os.getcwd(), "browser_storage")
        storage_file = os.path.join(storage_dir, f"{account_name}_state.json")
        if os.path.exists(storage_file):
            try:
                os.remove(storage_file)
                self.logger.info(f"已删除账号 {account_name} 的浏览器存储状态文件")
            except Exception as e:
                self.logger.error(f"删除浏览器存储状态文件时发生错误: {e}")
        else:
            self.logger.debug(f"浏览器存储状态文件不存在: {storage_file}")

    async def edit_account(self, old_account_name, new_account_name, new_password):
        """
        编辑账号信息
        
        Args:
            old_account_name: 原账号名称
            new_account_name: 新账号名称
            new_password: 新密码
            
        Returns:
            bool: 操作是否成功
        """
        if old_account_name not in self.accounts:
            return False

        # 关闭现有浏览器实例
        await self.close_browser(old_account_name)

        # 如果新旧账号名不同，需要删除旧账号并添加新账号，同时更新用户数据目录
        if old_account_name != new_account_name:
            account_data = self.accounts[old_account_name]
            del self.accounts[old_account_name]
            self.accounts[new_account_name] = account_data

            # 更新用户数据目录
            old_user_data_dir = os.path.join(self.user_data_dir, old_account_name)
            new_user_data_dir = os.path.join(self.user_data_dir, new_account_name)
            if os.path.exists(old_user_data_dir):
                try:
                    shutil.move(old_user_data_dir, new_user_data_dir)
                    self.logger.info(f"成功更新用户数据目录: {old_account_name} -> {new_account_name}")
                except Exception as e:
                    self.logger.error(f"更新用户数据目录时发生错误: {e}")
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

    async def batch_refresh_cookies(self, account_names=None, max_workers=5):
        """
        使用多线程批量刷新cookies
        
        Args:
            account_names: 要刷新的账号列表,如果为None则刷新所有账号
            max_workers: 最大并发线程数
            
        Returns:
            dict: 包含刷新结果的字典
        """
        # 如果没有指定账号列表，则使用所有账号
        if account_names is None:
            account_names = list(self.accounts.keys())
            
        if not account_names:
            self.logger.warning("没有找到要刷新的账号")
            return {
                'results': {},
                'total': 0,
                'success': 0,
                'failed': 0
            }

        # 准备账号和密码列表
        account_list = []
        for name in account_names:
            password = self.accounts.get(name, {}).get('password')
            if password:
                account_list.append((name, password))
            else:
                self.logger.error(f"账号 {name} 没有密码")

        total = len(account_list)
        completed = Queue()  # 用于跟踪完成的任务数
        results = {}  # 存储结果
        max_workers = min(total, max_workers)  # 限制最大线程数

        def refresh_single_account(account_name, password):
            """单个账号的刷新操作"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(
                    self.refresh_account_cookies(account_name, password)
                )
                loop.close()
                
                results[account_name] = success
                completed.put(1)
                
                if success:
                    self.logger.info(f"账号 {account_name} cookies 刷新成功")
                else:
                    self.logger.error(f"账号 {account_name} cookies 刷新失败")
                    
            except Exception as e:
                self.logger.error(f"账号 {account_name} 刷新出错: {str(e)}")
                results[account_name] = False
                completed.put(1)

        # 使用线程池执行刷新操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = [
                executor.submit(refresh_single_account, account_name, password)
                for account_name, password in account_list
            ]
            # 等待所有任务完成
            concurrent.futures.wait(futures)

        # 统计结果
        success_count = sum(1 for success in results.values() if success)
        fail_count = total - success_count
        
        self.logger.info(f"""
        批量刷新完成
        总计: {total} 个账号
        成功: {success_count} 个
        失败: {fail_count} 个
        """)
        
        return {
            'results': results,
            'total': total,
            'success': success_count,
            'failed': fail_count
        }
