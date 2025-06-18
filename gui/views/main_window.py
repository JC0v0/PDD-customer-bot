import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout
from PyQt6.QtGui import QFont, QIcon
from qfluentwidgets import FluentWindow,qrouter, NavigationItemPosition
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SubtitleLabel

from .monitor_view import MonitorView
from .keyword_manager_view import KeywordManagerView
from .user_view import UserView
from .setting_view import SettingView


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)
        self.label.setFont(QFont("Microsoft YaHei", 24))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignmentFlag.AlignCenter)

        # 必须给子界面设置全局唯一的对象名
        self.setObjectName(text.replace(' ', '-'))

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('拼多多AI客服助手')
        self.setWindowIcon(QIcon("icon/图标智能客服.ico"))
        # 创建主要视图
        self.monitor_view = MonitorView(self)#消息监控
        self.keyword_manager_view = KeywordManagerView(self)#关键词管理
        self.user_manager_view = UserView(self)#用户管理
        self.settingInterface = SettingView(self)#设置

        # 初始化界面
        self.initNavigation()
        self.initWindow()

    # 初始化导航栏
    def initNavigation(self):
        self.navigationInterface.setExpandWidth(200)
        self.navigationInterface.setMinimumWidth(200)
        self.addSubInterface(self.monitor_view, FIF.CHAT, '消息监控')
        self.addSubInterface(self.keyword_manager_view, FIF.EDIT, '关键词管理')
        self.addSubInterface(self.user_manager_view, FIF.PEOPLE, '用户管理',NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)
        # 设置默认选中的界面
        qrouter.setDefaultRouteKey(self.navigationInterface, self.monitor_view.objectName())

    # 初始化窗口
    def initWindow(self):
        self.resize(1000, 800)
        self.setMinimumWidth(760)
        self.setMinimumHeight(600)
        self.center()

    # 将窗口移动到屏幕中央
    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft()) 