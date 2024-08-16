import PyInstaller.__main__
import os
import json

import selenium_stealth
# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 确保 config 目录存在
config_dir = os.path.join(current_dir, 'config')
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

# 构建配置文件的完整路径
account_cookies_path = os.path.join(config_dir, 'account_cookies.json')
account_status_path = os.path.join(config_dir, 'account_status.json')
config_py_path = os.path.join(current_dir, 'config.py')

# 创建或确保文件存在
def ensure_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    print(f"File exists: {file_path}")

ensure_file(account_cookies_path)
ensure_file(account_status_path)

# 确保 config.py 文件存在
if not os.path.exists(config_py_path):
    print(f"Warning: {config_py_path} does not exist!")

# chromedriver 路径
chromedriver_path = os.path.join(current_dir, 'chromedriver-win64', 'chromedriver.exe')
# 获取 selenium_stealth 的 JavaScript 文件路径
selenium_stealth_dir = os.path.dirname(selenium_stealth.__file__)
js_dir = os.path.join(selenium_stealth_dir, 'js')

# 运行 PyInstaller
PyInstaller.__main__.run([
    'main.py',
    '--name=拼多多客服系统',
    '--onefile',
    '--windowed',
    f'--add-data={account_cookies_path};config',
    f'--add-data={account_status_path};config',
    f'--add-data={config_py_path};.',
    f'--add-binary={chromedriver_path};chromedriver-win64',
    f'--add-data={js_dir};selenium_stealth/js',
    '--icon=PddWorkbench.ico',
    '--hidden-import=config',
    '--debug=all',
    '--clean',
    '--hidden-import=selenium',
    '--hidden-import=selenium_stealth',
    '--collect-all=selenium_stealth'
])