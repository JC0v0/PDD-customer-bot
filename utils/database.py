from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
import os

def get_base_path():
    """
    获取应用的基础路径
    返回可执行文件所在目录或开发环境的项目根目录
    """
    if getattr(sys, 'frozen', False):
        # 如果是打包环境，使用可执行文件所在目录
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境，使用项目根目录
        return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# 获取基础路径
basedir = get_base_path()

# 创建Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'conversations.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy()
db.init_app(app) 