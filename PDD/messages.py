from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    role: str
    uid: str
    mall_id: Optional[str] = None
    csid: Optional[str] = None
    cs_uid: Optional[str] = None

@dataclass
class Message:
    data: Union[Dict[str, Any], tuple] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.data, tuple):
            if len(self.data) == 1 and isinstance(self.data[0], dict):
                self.data = self.data[0]
            else:
                self.data = {}

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], tuple]) -> 'Message':
        return cls(data)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default) if isinstance(self.data, dict) else default

    @property
    def from_user(self) -> User:
        from_data = self.get('from', {})
        if isinstance(from_data, dict):
            return User(
                role=from_data.get('role', 'unknown'),
                uid=from_data.get('uid', 'unknown'),
                mall_id=from_data.get('mall_id'),
                csid=from_data.get('csid'),
                cs_uid=from_data.get('cs_uid')
            )
        return User(role="unknown", uid="unknown")

    @property
    def to_user(self) -> User:
        to_data = self.get('to', {})
        if isinstance(to_data, dict):
            return User(
                role=to_data.get('role', 'unknown'),
                uid=to_data.get('uid', 'unknown'),
                mall_id=to_data.get('mall_id'),
                csid=to_data.get('csid'),
                cs_uid=to_data.get('cs_uid')
            )
        return User(role="unknown", uid="unknown")

    @property
    def content(self) -> str:
        return self.get('content', '')

    @property
    def msg_id(self) -> str:
        return self.get('msg_id', '')

    @property
    def timestamp(self) -> datetime:
        return datetime.fromtimestamp(int(self.get('ts', '0')))

    @property
    def type(self) -> int:
        return self.get('type', 0)

    @property
    def status(self) -> str:
        return self.get('status', '')

    @property
    def is_read(self) -> bool:
        return self.get('is_read') == 1

    @property
    def is_aut(self) -> bool:
        return self.get('is_aut') == 1

    @property
    def manual_reply(self) -> bool:
        return self.get('manual_reply') == 1

    @property
    def mallName(self) -> str:
        return self.get('mallName', '')

    @property
    def version(self) -> int:
        return self.get('version', 0)

    @property
    def cs_type(self) -> Optional[int]:
        return self.get('cs_type')

    @property
    def source_id(self) -> Optional[int]:
        return self.get('source_id')

    @property
    def template_name(self) -> Optional[str]:
        return self.get('template_name')

    @property
    def biz_context(self) -> Dict[str, Any]:
        return self.get('biz_context', {})

    @property
    def pre_msg_id(self) -> Optional[str]:
        return self.get('pre_msg_id')

    @property
    def show_auto(self) -> bool:
        return self.get('show_auto', False)

    @property
    def mall_context(self) -> Dict[str, Any]:
        return self.get('mall_context', {})

    @property
    def user_info(self) -> Dict[str, Any]:
        return self.get('user_info', {})

    @property
    def last_unreply_time(self) -> int:
        return self.get('last_unreply_time', 0)

    @property
    def info(self) -> Dict[str, Any]:
        return self.get('info', {})

    def is_goods_card(self) -> bool:
        return self.template_name == 'user_goods_card'

    def get_goods_info(self) -> Optional[Dict[str, Any]]:
        return self.info if self.is_goods_card() else None

    def get_goods_name(self) -> Optional[str]:
        return self.info.get('goodsName')

    def get_goods_price(self) -> Optional[str]:
        return self.info.get('goodsPrice')

    def get_goods_thumb_url(self) -> Optional[str]:
        return self.info.get('goodsThumbUrl')

    def get_sales_tip(self) -> Optional[str]:
        return self.info.get('salesTip')

    def get_goods_tags(self) -> List[Dict[str, Any]]:
        return self.info.get('tagList', [])

    def get_service_tags(self) -> List[str]:
        return self.info.get('serviceTags', {}).get('tags', [])

    def get_goods_id(self) -> Optional[int]:
        return self.info.get('goodsID')