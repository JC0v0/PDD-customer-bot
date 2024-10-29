from PIL import Image, ImageTk
import os
import sys
from utils.logger import get_logger, get_log_queue

class IconLoader:
    def __init__(self):
        self.logger = get_logger('icon_loader')
        self.log_queue = get_log_queue()
        self.add_icon = self.load_icon('person_add.png')
        self.remove_icon = self.load_icon('delete.png')
        self.refresh_icon = self.load_icon('autorenew.png')

    def load_icon(self, filename):
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            current_dir = sys._MEIPASS
        else:
            # 如果是开发环境
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(current_dir, 'icon', filename)
        return self.resize_image(icon_path, (24, 24))

    def resize_image(self, image_path, size):
        try:
            image = Image.open(image_path)
            image = image.resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        except FileNotFoundError:
            self.logger.error(f"无法找到图标文件: {image_path}")
            return None
