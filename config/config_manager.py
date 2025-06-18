import json
import os
from typing import Dict, Any, Optional
from utils.logger import get_logger


class ConfigManager:
    def __init__(self, config_path: str = "config/config.json"):
        """
        配置管理器初始化
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.logger = get_logger('config_manager')
        self._config_data = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置数据字典
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
                    self.logger.info(f"成功加载配置文件: {self.config_path}")
            else:
                self.logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._config_data = self._get_default_config()
                self.save_config()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            self._config_data = self._get_default_config()
        
        return self._config_data
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"配置已保存到: {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值
        """
        return self._config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置项
        
        Args:
            key: 配置键名
            value: 配置值
            
        Returns:
            设置是否成功
        """
        try:
            self._config_data[key] = value
            self.logger.info(f"设置配置项 {key} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"设置配置项失败: {str(e)}")
            return False
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """
        批量更新配置项
        
        Args:
            updates: 要更新的配置字典
            
        Returns:
            更新是否成功
        """
        try:
            self._config_data.update(updates)
            self.logger.info(f"批量更新配置项: {list(updates.keys())}")
            return True
        except Exception as e:
            self.logger.error(f"批量更新配置项失败: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除配置项
        
        Args:
            key: 配置键名
            
        Returns:
            删除是否成功
        """
        try:
            if key in self._config_data:
                del self._config_data[key]
                self.logger.info(f"删除配置项: {key}")
                return True
            else:
                self.logger.warning(f"配置项不存在: {key}")
                return False
        except Exception as e:
            self.logger.error(f"删除配置项失败: {str(e)}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置项
        
        Returns:
            所有配置数据
        """
        return self._config_data.copy()
    
    def reload(self) -> Dict[str, Any]:
        """
        重新加载配置文件
        
        Returns:
            重新加载后的配置数据
        """
        self.logger.info("重新加载配置文件")
        return self.load_config()
    
    def reset_to_default(self) -> bool:
        """
        重置为默认配置
        
        Returns:
            重置是否成功
        """
        try:
            self._config_data = self._get_default_config()
            self.logger.info("配置已重置为默认值")
            return True
        except Exception as e:
            self.logger.error(f"重置配置失败: {str(e)}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "getAssignCsList_url": "https://mms.pinduoduo.com/latitude/assign/getAssignCsList",
            "move_conversation_url": "https://mms.pinduoduo.com/plateau/chat/move_conversation",
            "coze_token": "",
            "coze_bot_id": "",
            "account_name": "",
            "password": ""
        }
    
    # 便捷方法，用于获取特定配置项
    @property
    def getAssignCsList_url(self) -> str:
        return self.get("getAssignCsList_url", "")
    
    @getAssignCsList_url.setter
    def getAssignCsList_url(self, value: str):
        self.set("getAssignCsList_url", value)
    
    @property
    def move_conversation_url(self) -> str:
        return self.get("move_conversation_url", "")
    
    @move_conversation_url.setter
    def move_conversation_url(self, value: str):
        self.set("move_conversation_url", value)
    
    @property
    def coze_token(self) -> str:
        return self.get("coze_token", "")
    
    @coze_token.setter
    def coze_token(self, value: str):
        self.set("coze_token", value)
    
    @property
    def coze_bot_id(self) -> str:
        return self.get("coze_bot_id", "")
    
    @coze_bot_id.setter
    def coze_bot_id(self, value: str):
        self.set("coze_bot_id", value)
    
    @property
    def account_name(self) -> str:
        return self.get("account_name", "")
    
    @account_name.setter
    def account_name(self, value: str):
        self.set("account_name", value)
    
    @property
    def password(self) -> str:
        return self.get("password", "")
    
    @password.setter
    def password(self, value: str):
        self.set("password", value)


# 创建全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """
    获取配置管理器实例
    
    Returns:
        ConfigManager实例
    """
    return config_manager 