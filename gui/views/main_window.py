import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFrame, QStackedWidget
from qfluentwidgets import FluentWindow, NavigationInterface, qrouter
from qfluentwidgets import FluentIcon as FIF

from .monitor_view import MonitorView
from .keyword_manager_view import KeywordManagerView
from .account_manager_view import AccountManagerView


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('拼多多AI客服助手')
        
        # 创建主要视图
        self.monitor_view = MonitorView(self)
        self.keyword_manager_view = KeywordManagerView(self)
        self.account_manager_view = AccountManagerView(self)

        # 添加子页面到堆叠窗口
        self.addSubInterface(self.account_manager_view, FIF.PEOPLE, '账号管理')
        self.addSubInterface(self.monitor_view, FIF.CHAT, '消息监控')
        self.addSubInterface(self.keyword_manager_view, FIF.EDIT, '关键词管理')

        # 初始化界面
        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.navigationInterface.setExpandWidth(200)
        self.navigationInterface.setMinimumWidth(200)
        
        # 设置默认选中的界面
        qrouter.setDefaultRouteKey(self.navigationInterface, self.account_manager_view.objectName())

    def initWindow(self):
        self.resize(1000, 800)
        self.setMinimumWidth(760)
        self.setMinimumHeight(600)
        self.center()

    def center(self):
        # 将窗口移动到屏幕中央
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft()) 