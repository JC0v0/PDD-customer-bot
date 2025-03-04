from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                          QScrollArea, QFrame, QGridLayout, QDialog, QMenu, QCheckBox)
from qfluentwidgets import (CardWidget, PushButton, PrimaryPushButton,
                          InfoBar, InfoBarPosition, FluentIcon, MessageBox,
                          LineEdit, IconWidget, FlowLayout, SubtitleLabel,
                          StrongBodyLabel, MenuAnimationType, RoundMenu,
                          Action, FluentStyleSheet, PasswordLineEdit,
                          ExpandLayout, icon)
import json
import os
import asyncio
from datetime import datetime, timezone
from PDD.account_manager import AccountManager
from PDD.Set_up_online import batch_set_csstatus
from PDD.Set_up_online import set_csstatus
from utils.logger import get_logger

def run_async(coro):
    """运行异步任务的辅助函数"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

class AccountDialog(QDialog):
    def __init__(self, parent=None, account_name="", password="", is_edit=False):
        super().__init__(parent=parent)
        self.setWindowTitle('编辑账号' if is_edit else '添加账号')
        self.resize(400, 200)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 标题
        title = SubtitleLabel('编辑账号' if is_edit else '添加账号', self)
        layout.addWidget(title)
        
        # 提示文本
        hint = StrongBodyLabel('请输入账号信息', self)
        layout.addWidget(hint)
        
        # 创建输入框
        self.username_edit = LineEdit(self)
        self.username_edit.setPlaceholderText('请输入账号')
        if account_name:
            self.username_edit.setText(account_name)
            
        self.password_edit = PasswordLineEdit(self)
        self.password_edit.setPlaceholderText('请输入密码')
        if password:
            self.password_edit.setText(password)
        
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_edit)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.cancel_button = PushButton('取消', self)
        self.ok_button = PrimaryPushButton('确定', self)
        
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # 设置布局
        self.setLayout(layout)
        
    def get_account_info(self):
        return self.username_edit.text(), self.password_edit.text()


class AccountCard(CardWidget):
    def __init__(self, username, status, expiry_date, parent=None):
        super().__init__(parent)
        self.username = username
        self.status = status
        self.expiry_date = expiry_date
        self.initUI()
        
    def initUI(self):
        layout = QHBoxLayout(self)  
        layout.setContentsMargins(16, 16, 16, 16)  
        
        # 头像图标
        avatar = IconWidget("icon/PddWorkbench.ico", self)
        avatar.setFixedSize(32, 32)
        
        # 用户信息垂直布局
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)  
        
        # 用户名
        username_label = QLabel(self.username, self)
        username_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        
        # 状态
        status_label = QLabel(self.status, self)
        status_color = '#4CAF50' if self.status == '正常' else '#FFC107'
        status_label.setStyleSheet(f'color: {status_color}; font-size: 14px;')
        
        # 过期时间
        expiry_label = QLabel(self.expiry_date, self)
        expiry_label.setStyleSheet('color: #666666; font-size: 12px;')
        
        info_layout.addWidget(username_label)
        info_layout.addWidget(status_label)
        info_layout.addWidget(expiry_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  
        
        # 刷新按钮
        self.refresh_button = PushButton('刷新Cookies', self)
        
        # 状态设置按钮
        self.status_button = PushButton('状态', self, icon=FluentIcon.SETTING)
        self.status_button.setFixedWidth(80)
        
        # 编辑按钮
        self.edit_button = PushButton('编辑', self, icon=FluentIcon.EDIT)
        self.edit_button.setFixedWidth(80)
        
        # 删除按钮
        self.delete_button = PushButton('删除', self, icon=FluentIcon.DELETE)
        self.delete_button.setFixedWidth(80)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.status_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        
        # 添加到主布局
        layout.addWidget(avatar)
        layout.addSpacing(16)  
        layout.addLayout(info_layout)
        layout.addStretch()  
        layout.addLayout(button_layout)
        
        # 设置卡片大小和样式
        self.setFixedHeight(90)  
        self.setMinimumWidth(600)  
        
        # 创建状态菜单
        self.status_menu = RoundMenu(parent=self)
        self.status_menu.addAction(Action(FluentIcon.ACCEPT, '在线'))
        self.status_menu.addAction(Action(FluentIcon.PAUSE, '忙碌'))
        self.status_menu.addAction(Action(FluentIcon.CLOSE, '离线'))
        
        # 连接状态按钮点击事件
        self.status_button.clicked.connect(self.show_status_menu)
        
    def show_status_menu(self):
        # 显示状态菜单
        pos = self.status_button.mapToGlobal(self.status_button.rect().bottomLeft())
        self.status_menu.exec(pos)


class AccountManagerView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('accountManagerView')
        self.logger = get_logger('account_manager')
        self.account_manager = AccountManager()
        self.accounts = []
        self.current_account = None
        
        self.initUI()
        self.load_accounts()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)  
        main_layout.setContentsMargins(16, 16, 16, 16)  
        
        # 标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel('账号管理', self)
        title_label.setStyleSheet('font-size: 24px; font-weight: bold;')
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  
        
        self.add_button = PrimaryPushButton('添加账号', self, icon=FluentIcon.ADD)
        self.refresh_button = PushButton('刷新列表', self, icon=FluentIcon.SYNC)
        self.refresh_all_cookies_button = PushButton('刷新所有Cookies', self, icon=FluentIcon.SYNC)
        self.status_button = PushButton('批量设置状态', self ,icon=FluentIcon.SETTING)
        
        # 先添加伸缩器，使按钮靠右
        button_layout.addStretch()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.refresh_all_cookies_button)
        button_layout.addWidget(self.status_button)
        
        # 标题靠左，按钮靠右
        title_layout.addWidget(title_label)
        title_layout.addLayout(button_layout, stretch=1)  
        
        main_layout.addLayout(title_layout)
        
        # 创建滚动区域
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # 创建滚动区域的内容容器
        self.scroll_content = QWidget(scroll)
        self.cards_layout = QVBoxLayout(self.scroll_content)  
        self.cards_layout.setSpacing(8)  
        self.cards_layout.setContentsMargins(0, 0, 0, 0)  
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  
        
        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll)
        
        # 连接信号
        self.add_button.clicked.connect(self.add_account)
        self.refresh_button.clicked.connect(self.load_accounts)
        self.refresh_all_cookies_button.clicked.connect(
            lambda: run_async(self.refresh_all_cookies())
        )
        self.status_button.clicked.connect(self.show_status_allmenu)
        
    def load_accounts(self):
        self.accounts = []
        for account_name, data in self.account_manager.accounts.items():
            expiry_date = data.get('expiry_date', '')
            if expiry_date:
                expiry_date = datetime.fromisoformat(expiry_date)
                expiry_date_str = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                expiry_date_str = "未设置"
                
            self.accounts.append({
                'username': account_name,
                'password': data.get('password', ''),
                'status': data.get('status', '未设置'),
                'expiry_date': expiry_date_str
            })
        self.update_account_cards()
        
    def update_account_cards(self):
        # 清除现有卡片
        for i in reversed(range(self.cards_layout.count())):
            item = self.cards_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                self.cards_layout.takeAt(i)
        
        # 添加新卡片
        for account in self.accounts:
            card = AccountCard(
                account['username'],
                account['status'],
                account['expiry_date'],
                self
            )
            # 连接按钮信号
            card.delete_button.clicked.connect(
                lambda checked, account=account: self.delete_account(account)
            )
            card.edit_button.clicked.connect(
                lambda checked, account=account: self.edit_account(account)
            )
            card.status_menu.triggered.connect(
                lambda action, account=account: self.set_account_status(account, action.text())
            )
            card.refresh_button.clicked.connect(
                lambda checked, account=account: run_async(self.refresh_selected_cookies(account))
            )
            
            self.cards_layout.addWidget(card)
            
        # 添加弹性空间
        self.cards_layout.addStretch()
        
    def add_account(self):
        dialog = AccountDialog(self)
        if dialog.exec():
            username, password = dialog.get_account_info()
            if username and password:
                # 使用同步方式添加账号
                run_async(self.account_manager.add_account(username, password))
                self.load_accounts()
            else:
                InfoBar.warning(
                    title='添加失败',
                    content='账号和密码不能为空',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                
    def edit_account(self, account):
        dialog = AccountDialog(
            self,
            account['username'],
            account['password'],
            is_edit=True
        )
        if dialog.exec():
            new_username, new_password = dialog.get_account_info()
            if new_username and new_password:
                run_async(
                    self.account_manager.edit_account(
                        account['username'],
                        new_username,
                        new_password
                    )
                )
                self.load_accounts()
                
    def delete_account(self, account):
        box = MessageBox(
            '删除确认',
            '确定要删除这个账号吗？',
            self
        )
        if box.exec():
            run_async(self.account_manager.remove_account(account['username']))
            self.load_accounts()
            
    def set_account_status(self, account, status):
        account_data = self.account_manager.accounts.get(account['username'])
        if account_data:
            result = set_csstatus(account['username'], account_data, status)
            if result and result.get('success'):
                self.logger.info(f"账号 {account['username']} 状态设置成功: {status}")
                self.account_manager.accounts[account['username']]['status'] = status
                self.load_accounts()
                
                InfoBar.success(
                    title='设置成功',
                    content=f'账号状态已设置为: {status}',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title='设置失败',
                    content='账号状态设置失败',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                
    async def refresh_all_cookies(self):
        """刷新所有账号的cookies"""
        if not self.accounts:
            InfoBar.error(
                title='错误',
                content="没有找到任何账号",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 获取所有账号名称
        account_names = [account['username'] for account in self.accounts if account.get('username')]
        
        # 使用batch_refresh_cookies_mt刷新所有账号
        result = await self.account_manager.batch_refresh_cookies(account_names)
        
        if result['success'] > 0:
            InfoBar.success(
                title='刷新完成',
                content=f"成功刷新 {result['success']}/{result['total']} 个账号",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        
        if result['failed'] > 0:
            InfoBar.error(
                title='部分失败',
                content=f"有 {result['failed']} 个账号刷新失败",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        # 刷新完成后更新账号列表
        self.load_accounts()

    async def refresh_selected_cookies(self, account):
        """刷新选中账号的cookies"""
        username = account.get('username', '')
        if not username:
            return
            
        if not self.account_manager.is_refreshing(username):
            try:
                success = await self.account_manager.refresh_account_cookies(username)
                if success:
                    InfoBar.success(
                        title='成功',
                        content=f"账号 {username} cookies刷新成功",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title='错误',
                        content=f"账号 {username} cookies刷新失败",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title='错误',
                    content=f"账号 {username} cookies刷新出错: {str(e)}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        else:
            InfoBar.warning(
                title='正在刷新',
                content=f'账号 {username} 正在刷新中',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def show_status_allmenu(self):
        """显示状态设置菜单"""
        menu = RoundMenu(parent=self)
        menu.addAction(Action('在线', self, triggered=lambda: self.batch_set_status("在线")))
        menu.addAction(Action('忙碌', self, triggered=lambda: self.batch_set_status("忙碌")))
        menu.addAction(Action('离线', self, triggered=lambda: self.batch_set_status("离线")))
        menu.exec(self.status_button.mapToGlobal(self.status_button.rect().bottomLeft()))
        
    def batch_set_status(self, status):
        """批量设置账号状态"""
        try:
            batch_set_csstatus(status)
            # 更新所有账号的状态
            for username in self.account_manager.accounts:
                self.account_manager.accounts[username]['status'] = status
                
            self.load_accounts()
            
            InfoBar.success(
                title='设置成功',
                content=f"已将所有账号状态设置为: {status}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            self.logger.error(f"批量设置状态时发生错误: {str(e)}")
            InfoBar.error(
                title='错误',
                content=f"设置状态失败: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )