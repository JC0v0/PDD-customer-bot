import logging
import queue

# 创建一个队列来存储日志消息
log_queue = queue.Queue()

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:  # 只有在没有处理器时才添加
        logger.setLevel(logging.INFO)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建队列处理器
        queue_handler = QueueHandler(log_queue)
        queue_handler.setLevel(logging.INFO)

        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        queue_handler.setFormatter(formatter)

        # 添加处理器到logger
        logger.addHandler(console_handler)
        logger.addHandler(queue_handler)

    return logger

def get_logger(name):
    return setup_logger(name)

def get_log_queue():
    return log_queue
