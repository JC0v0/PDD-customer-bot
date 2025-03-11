@echo off
echo 正在启动拼多多AI客服应用...

:: 激活虚拟环境（请根据实际路径修改）
call .venv\Scripts\activate.bat
:: 如果您的虚拟环境在其他位置，请修改上面的路径
:: 例如: call C:\path\to\your\venv\Scripts\activate.bat

:: 使用pythonw启动应用程序（没有命令行窗口）
start "" pythonw main.py

:: 等待3秒
timeout /t 3 /nobreak

:: 快速关闭此批处理窗口
exit 