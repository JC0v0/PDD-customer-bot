import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from PDD.pdd_message import PDDChatMessage
logger = get_logger(__name__)
data = {
  "message": {
    "content": "对方撤回了一条消息",
    "from": {
      "role": "user",
      "uid": "6840347447"
    },
    "info": {
      "msg_id": "1747284411074",
      "update_type": 3,
      "withdraw_hint": "对方撤回了一条消息"
    },
    "msg_id": "1747284413543",
    "nickname": "景**",
    "to": {
      "mall_id": "877317613",
      "role": "mall_cs",
      "uid": "877317613"
    },
    "ts": "1747284413",
    "type": 1002
  },
  "request_id": "1747284413543",
  "response": "push",
  "result": "ok",
  "target": {
    "mall_id": "877317613",
    "mms_uid": "149439587"
  }
}


msg = PDDChatMessage(data)

logger.info(f"用户消息类型:{msg.user_msg_type},内容:{msg.content}")
