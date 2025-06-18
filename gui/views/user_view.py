from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy
from qfluentwidgets import (LineEdit, PasswordLineEdit, PrimaryPushButton, PushButton,
                          FluentIcon, InfoBar, InfoBarPosition, ProgressBar,
                          TitleLabel, SubtitleLabel, BodyLabel, CardWidget, 
                          StrongBodyLabel, CaptionLabel)
import asyncio
import traceback
from PDD.pdd_login import PDDLogin
from utils.logger import get_logger


class LoginThread(QThread):
    """登录线程"""
    finished = pyqtSignal(bool)  # 登录结果
    error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, account_name, password):
        super().__init__()
        self.account_name = account_name
        self.password = password
        self.logger = get_logger('user_login')
        
    def run(self):
        """执行登录"""
        try:
            # 创建异步事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 更新配置文件中的账号密码
            self.update_config()
            
            # 执行登录
            login = PDDLogin()
            result = loop.run_until_complete(login.login())
            
            loop.close()
            self.finished.emit(result)
            
        except Exception as e:
            self.logger.error(f"登录异常: {e}")
            self.error.emit(str(e))
            traceback.print_exc()
            
    def update_config(self):
        """更新配置文件中的账号密码"""
        try:
            config_path = 'config/config.py'
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换账号名和密码
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('account_name ='):
                    lines[i] = f'account_name = "{self.account_name}"'
                elif line.strip().startswith('password ='):
                    lines[i] = f'password = "{self.password}"'
            
            # 写回文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
                
            self.logger.info("配置文件已更新")
            
        except Exception as e:
            self.logger.error(f"更新配置文件失败: {e}")


class UserView(QWidget):
    """用户管理界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('userView')
        self.logger = get_logger('user_view')
        self.login_thread = None
        
        self.initUI()
        
    def initUI(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题区域
        title_layout = QVBoxLayout()
        title_layout.setSpacing(8)
        
        self.title_label = TitleLabel("账号登录", self)
        self.subtitle_label = SubtitleLabel("请输入拼多多商户账号信息", self)
        self.subtitle_label.setStyleSheet("color: #666;")
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        
        # 登录卡片
        self.login_card = CardWidget(self)
        card_layout = QVBoxLayout(self.login_card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(40, 30, 40, 30)
        
        # 表单区域
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        form_layout.setColumnStretch(1, 1)
        
        # 账号输入
        account_label = StrongBodyLabel("商户账号:", self)
        self.account_input = LineEdit(self)
        self.account_input.setPlaceholderText("请输入店铺名称或商户账号")
        self.account_input.setFixedHeight(40)
        
        # 密码输入
        password_label = StrongBodyLabel("登录密码:", self)
        self.password_input = PasswordLineEdit(self)
        self.password_input.setPlaceholderText("请输入登录密码")
        self.password_input.setFixedHeight(40)
        
        # 添加到表单布局
        form_layout.addWidget(account_label, 0, 0, Qt.AlignmentFlag.AlignRight)
        form_layout.addWidget(self.account_input, 0, 1)
        form_layout.addWidget(password_label, 1, 0, Qt.AlignmentFlag.AlignRight)
        form_layout.addWidget(self.password_input, 1, 1)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.login_button = PrimaryPushButton("登录", self, FluentIcon.ACCEPT)
        self.login_button.setFixedHeight(40)
        self.login_button.setFixedWidth(120)
        
        self.clear_button = PushButton("清空", self, FluentIcon.DELETE)
        self.clear_button.setFixedHeight(40)
        self.clear_button.setFixedWidth(80)
        
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.login_button)
        
        # 进度条
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setVisible(False)
        
        # 状态标签
        self.status_label = BodyLabel("请输入账号密码进行登录", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; padding: 10px;")
        
        # 添加到卡片布局
        card_layout.addLayout(form_layout)
        card_layout.addWidget(self.progress_bar)
        card_layout.addLayout(button_layout)
        card_layout.addWidget(self.status_label)
        
        # 登录历史/状态区域
        self.info_card = CardWidget(self)
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(20, 20, 20, 20)
        
        info_title = StrongBodyLabel("登录说明", self)
        info_content = BodyLabel(
            "• 请使用拼多多商家后台的账号密码\n"
            "• 登录成功后将自动保存配置信息\n"
            "• 系统将通过浏览器自动化完成登录\n"
            "• 登录过程可能需要1-2分钟，请耐心等待",
            self
        )
        info_content.setStyleSheet("color: #666; line-height: 1.5;")
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_content)
        
        # 添加到主布局
        main_layout.addLayout(title_layout)
        main_layout.addWidget(self.login_card)
        main_layout.addWidget(self.info_card)
        main_layout.addStretch()
        
        # 连接信号
        self.login_button.clicked.connect(self.on_login_clicked)
        self.clear_button.clicked.connect(self.on_clear_clicked)
        self.account_input.returnPressed.connect(self.on_login_clicked)
        self.password_input.returnPressed.connect(self.on_login_clicked)
        
        # 从配置文件读取已保存的账号
        self.load_saved_account()
        
    def load_saved_account(self):
        """从配置文件加载已保存的账号"""
        try:
            with open('config/config.py', 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line in content.split('\n'):
                if line.strip().startswith('account_name ='):
                    account_name = line.split('=')[1].strip().strip('"')
                    if account_name and account_name != "请填写账号名":
                        self.account_input.setText(account_name)
                        break
                        
        except Exception as e:
            self.logger.warning(f"加载已保存账号失败: {e}")
            
    def on_login_clicked(self):
        """登录按钮点击事件"""
        account = self.account_input.text().strip()
        password = self.password_input.text().strip()
        
        if not account:
            self.show_error("请输入商户账号")
            return
            
        if not password:
            self.show_error("请输入登录密码")
            return
            
        # 开始登录
        self.start_login(account, password)
        
    def on_clear_clicked(self):
        """清空按钮点击事件"""
        self.account_input.clear()
        self.password_input.clear()
        self.status_label.setText("请输入账号密码进行登录")
        self.status_label.setStyleSheet("color: #666; padding: 10px;")
        
    def start_login(self, account, password):
        """开始登录过程"""
        self.logger.info(f"开始登录，账号: {account}")
        
        # 禁用输入控件
        self.account_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.login_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 更新状态
        self.status_label.setText("正在登录，请稍候...")
        self.status_label.setStyleSheet("color: #1890ff; padding: 10px;")
        
        # 创建并启动登录线程
        self.login_thread = LoginThread(account, password)
        self.login_thread.finished.connect(self.on_login_finished)
        self.login_thread.error.connect(self.on_login_error)
        self.login_thread.start()
        
        # 设置超时定时器
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.on_login_timeout)
        self.timeout_timer.start(120000)  # 120秒超时
        
        # 显示开始信息
        InfoBar.info(
            title='开始登录',
            content='正在启动浏览器进行登录...',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
    def on_login_finished(self, success):
        """登录完成"""
        self.timeout_timer.stop()
        
        if success:
            self.logger.info("登录成功")
            self.status_label.setText("登录成功！配置已保存")
            self.status_label.setStyleSheet("color: #52c41a; padding: 10px;")
            
            InfoBar.success(
                title='登录成功',
                content='账号登录成功，配置信息已保存',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        else:
            self.logger.error("登录失败")
            self.on_login_error("登录失败，请检查账号密码或网络连接")
            
        # 恢复控件状态
        self.reset_ui()
            
    def on_login_error(self, error_msg):
        """登录错误"""
        self.timeout_timer.stop()
        self.logger.error(f"登录错误: {error_msg}")
        
        # 恢复控件状态
        self.reset_ui()
        
        # 显示错误信息
        self.show_error(error_msg)
        
    def on_login_timeout(self):
        """登录超时"""
        self.logger.warning("登录超时")
        
        # 停止登录线程
        if self.login_thread and self.login_thread.isRunning():
            self.login_thread.terminate()
            self.login_thread.wait(1000)
            
        # 恢复控件状态
        self.reset_ui()
        
        # 显示超时错误
        self.show_error("登录超时，请检查网络连接后重试")
        
    def reset_ui(self):
        """重置UI状态"""
        self.account_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.login_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if not self.status_label.text().startswith("登录成功"):
            self.status_label.setText("请输入账号密码进行登录")
            self.status_label.setStyleSheet("color: #666; padding: 10px;")
        
    def show_error(self, message):
        """显示错误信息"""
        self.status_label.setText(f"错误: {message}")
        self.status_label.setStyleSheet("color: #ff4d4f; padding: 10px;")
        
        # 创建InfoBar显示错误
        InfoBar.error(
            title='登录失败',
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        
    def closeEvent(self, event):
        """关闭事件"""
        # 停止登录线程
        if self.login_thread and self.login_thread.isRunning():
            self.login_thread.terminate()
            self.login_thread.wait(1000)
            
        # 停止定时器
        if hasattr(self, 'timeout_timer'):
            self.timeout_timer.stop()
            
        super().closeEvent(event)
