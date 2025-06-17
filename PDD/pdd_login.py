"""
拼多多账号异步登录认证
"""
import json
import os

from utils.logger import get_logger
from playwright.async_api import async_playwright

class PDDLogin():
    def __init__(self):
        self.logger = get_logger(__name__)
        self.base_url = "https://mms.pinduoduo.com/home"

    async def login(self,name,password):
        """使用账号密码登录
        
        Args:
            name: 账号名称
            password: 账号密码

        """
        try:
            # 启动Playwright
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-notifications',  # 禁用通知
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # 创建上下文和页面
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            # 访问登录页面
            await page.goto(self.base_url)
            
            # 点击账号密码登录
            await page.click("div.tab-item.last-item:has-text('账号登录')")
            
            # 等待页面加载
            await page.wait_for_selector("input[type='text']")
            
            # 输入店铺名
            await page.fill("input[type='text']", name)
            
            # 输入密码
            await page.fill("input[type='password']", password)
            
            # 点击登录按钮
            await page.click("button:has-text('登录')")
            
            # 等待登录成功
            await page.wait_for_url("**/home", timeout=30000)
            
            # 获取cookies并转换为字典格式
            cookies_list = await context.cookies()
            # 将playwright格式的cookies列表转换为字典格式
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}
            cookies_json = json.dumps(cookies_dict)
            
            # 将cookies保存到config/cookies.json文件
            with open('config/cookies.json', 'w', encoding='utf-8') as f:
                f.write(cookies_json)
            
            # 关闭浏览器
            await browser.close()
            await playwright.stop()
                
            return True
            
        except Exception as e:
            self.logger.error(f"登录失败: {str(e)}")
            return False
