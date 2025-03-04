@echo off
echo 正在启动拼多多AI客服应用...

:: 激活虚拟环境（请根据实际路径修改）
call .venv\Scripts\activate.bat

start "" pythonw main.py

:: 等待3秒
timeout /t 3 /nobreak

:: 快速关闭此批处理窗口
exit 