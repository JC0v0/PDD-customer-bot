# PDD Package
"""
拼多多客服机器人模块包
"""

from .pdd_login import PDDLogin
from .pdd_message import PDDChatMessage

__all__ = [
    'PDDLogin',  
    'PDDChatMessage'       
] 