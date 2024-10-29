import json
import re
from utils.logger import get_logger
logger = get_logger('keyword_transfer')
class KeywordTransfer:
    def __init__(self, file_path='config/keywords.json'):
        self.file_path = file_path
        self.keywords, self.regex_patterns = self.load_keywords()

    def load_keywords(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                keywords = data.get('human_service_keywords', [])
                regex_patterns = data.get('regex_patterns', [])
                compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in regex_patterns]
                return keywords, compiled_patterns
        except FileNotFoundError:
            logger.info("未找到关键词文件,使用默认关键词")
            return ['转人工', '人工客服', '真人', '客服', '人工'], []
        except json.JSONDecodeError:
            logger.info("关键词文件格式错误,使用默认关键词")
            return ['转人工', '人工客服', '真人', '客服', '人工'], []

    def save_keywords(self, keywords, regex_patterns):
        data = {
            'human_service_keywords': keywords,
            'regex_patterns': regex_patterns
        }
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("关键词设置已保存")
            self.keywords, self.regex_patterns = keywords, [re.compile(pattern, re.IGNORECASE) for pattern in regex_patterns]
            return True
        except Exception as e:
            logger.error(f"保存关键词设置时出错：{str(e)}")
            return False

    def need_human_service(self, message_content):
        # 精确匹配
        if any(keyword in message_content for keyword in self.keywords):
            return True
        
        # 正则模糊匹配
        for pattern in self.regex_patterns:
            if pattern.search(message_content):
                return True
        
        return False
