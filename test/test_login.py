import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from PDD.pdd_login import PDDLogin

async def main():
    login = PDDLogin()
    result = await login.login()
    if result:
        print("登录成功！")
    else:
        print("登录失败！")

if __name__ == "__main__":
    asyncio.run(main())