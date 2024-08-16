import logging
import os
from logging.handlers import RotatingFileHandler
import queue

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

def setup_logger(name, log_file, level=logging.INFO, log_queue=None):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 文件处理器
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)

    # 获取logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)

    # 如果提供了队列,添加QueueHandler
    if log_queue:
        queue_handler = QueueHandler(log_queue)
        queue_handler.setFormatter(formatter)
        logger.addHandler(queue_handler)

    return logger

# 创建一个全局的日志队列
log_queue = queue.Queue()

# 创建主logger
main_logger = setup_logger('main', 'logs/main.log', log_queue=log_queue)

def get_logger(name):
    return setup_logger(name, f'logs/{name}.log', log_queue=log_queue)

def get_log_queue():
    return log_queue