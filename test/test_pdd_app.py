import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from PDD.pdd_app import PDDApp

async def main():
    pdd_app = PDDApp(account_name="葵花康复器械景诚")
    await pdd_app.start()

if __name__ == "__main__":
    asyncio.run(main())
