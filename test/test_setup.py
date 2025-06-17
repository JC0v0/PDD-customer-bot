# 测试设置在线状态
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PDD.Set_up_online import SetUpOnline

def test_set_csstatus():
    setup = SetUpOnline()
    setup.set_csstatus("在线")

if __name__ == "__main__":
    test_set_csstatus()