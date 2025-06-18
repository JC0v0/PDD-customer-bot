import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import threading
from PDD.pdd_app import PDDApp

async def main():
    # 创建停止事件（测试时可以传递None）
    stop_event = threading.Event()
    pdd_app = PDDApp(account_name="葵花康复器械景诚", stop_event=stop_event)
    await pdd_app.start()

if __name__ == "__main__":
    asyncio.run(main())
