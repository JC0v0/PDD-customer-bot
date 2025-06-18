from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from qfluentwidgets import (LineEdit, PrimaryPushButton, PushButton,
                          FluentIcon, InfoBar, InfoBarPosition,
                          TitleLabel, SubtitleLabel, BodyLabel, CardWidget, 
                          StrongBodyLabel, CaptionLabel, TextEdit, HyperlinkLabel)
from config.config_manager import get_config
from utils.logger import get_logger


class SettingView(QWidget):
    """设置界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('settingView')
        self.logger = get_logger('setting_view')
        self.config_manager = get_config()  # 获取配置管理器实例
        
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
        
        self.title_label = TitleLabel("系统设置", self)
        self.subtitle_label = SubtitleLabel("配置AI助手和系统参数", self)
        self.subtitle_label.setStyleSheet("color: #666;")
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        
        # Coze AI 配置卡片
        self.coze_card = CardWidget(self)
        coze_layout = QVBoxLayout(self.coze_card)
        coze_layout.setSpacing(20)
        coze_layout.setContentsMargins(30, 25, 30, 25)
        
        # Coze 配置标题
        coze_title = StrongBodyLabel("🤖 Coze AI 配置", self)
        coze_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        coze_layout.addWidget(coze_title)
        
        # 表单区域
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        form_layout.setColumnStretch(1, 1)
        
        # Coze Token 配置
        token_label = StrongBodyLabel("API Token:", self)
        self.token_input = LineEdit(self)
        self.token_input.setPlaceholderText("请输入 Coze API Token (以pat_开头)")
        self.token_input.setFixedHeight(40)
        
        # Bot ID 配置
        bot_id_label = StrongBodyLabel("Bot ID:", self)
        self.bot_id_input = LineEdit(self)
        self.bot_id_input.setPlaceholderText("请输入 Coze Bot ID (纯数字)")
        self.bot_id_input.setFixedHeight(40)
        
        # 添加到表单布局
        form_layout.addWidget(token_label, 0, 0, Qt.AlignmentFlag.AlignRight)
        form_layout.addWidget(self.token_input, 0, 1)
        form_layout.addWidget(bot_id_label, 1, 0, Qt.AlignmentFlag.AlignRight)
        form_layout.addWidget(self.bot_id_input, 1, 1)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_button = PrimaryPushButton("保存配置", self, FluentIcon.SAVE)
        self.save_button.setFixedHeight(40)
        self.save_button.setFixedWidth(120)
        
        self.reset_button = PushButton("重置", self, FluentIcon.SYNC)
        self.reset_button.setFixedHeight(40)
        self.reset_button.setFixedWidth(80)
        
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.save_button)
        
        # 状态标签
        self.status_label = BodyLabel("请配置 Coze AI 参数", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; padding: 10px;")
        
        # 添加到 Coze 卡片布局
        coze_layout.addLayout(form_layout)
        coze_layout.addLayout(button_layout)
        coze_layout.addWidget(self.status_label)
        
        # 帮助信息卡片
        self.help_card = CardWidget(self)
        help_layout = QVBoxLayout(self.help_card)
        help_layout.setContentsMargins(25, 20, 25, 20)
        help_layout.setSpacing(15)
        
        help_title = StrongBodyLabel("📖 配置说明", self)
        help_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        help_content = BodyLabel(
            "🔹 API Token: 访问 Coze 平台获取个人访问令牌\n"
            "🔹 Bot ID: 在 Coze 控制台中找到你的机器人ID\n"
            "🔹 配置保存后将自动应用到 AI 回复功能\n"
            "🔹 请确保 Token 有效并且 Bot 已发布",
            self
        )
        help_content.setStyleSheet("color: #666; line-height: 1.6;")
        
        # 帮助链接
        help_link = HyperlinkLabel('📚 查看 Coze 官方文档', self)
        help_link.setUrl('https://www.coze.cn/docs')
        help_link.setStyleSheet("color: #1890ff;")
        
        help_layout.addWidget(help_title)
        help_layout.addWidget(help_content)
        help_layout.addWidget(help_link)
        
        
        # 添加到主布局
        main_layout.addLayout(title_layout)
        main_layout.addWidget(self.coze_card)
        main_layout.addWidget(self.help_card)
        main_layout.addStretch()
        
        # 连接信号
        self.save_button.clicked.connect(self.on_save_clicked)
        self.reset_button.clicked.connect(self.on_reset_clicked)
        
        # 加载现有配置
        self.load_config()
        
    def load_config(self):
        """从配置文件加载配置"""
        try:
            # 使用配置管理器加载配置
            coze_token = self.config_manager.coze_token or ""
            coze_bot_id = self.config_manager.coze_bot_id or ""
            
            # 填充到输入框
            self.token_input.setText(coze_token)
            self.bot_id_input.setText(coze_bot_id)
            
            # 更新状态
            if coze_token and coze_bot_id:
                self.status_label.setText("配置已加载")
                self.status_label.setStyleSheet("color: #52c41a; padding: 10px;")
            else:
                self.status_label.setText("请完善配置信息")
                self.status_label.setStyleSheet("color: #fa8c16; padding: 10px;")
                
            self.logger.info("配置加载成功")
                
        except Exception as e:
            self.logger.warning(f"加载配置失败: {e}")
            self.show_error("配置加载失败")

            
    def on_save_clicked(self):
        """保存按钮点击事件"""
        coze_token = self.token_input.text().strip()
        coze_bot_id = self.bot_id_input.text().strip()
        
        if not coze_token:
            self.show_error("请输入 Coze API Token")
            return
            
        if not coze_bot_id:
            self.show_error("请输入 Coze Bot ID")
            return
            
        # 验证 Token 格式
        if not coze_token.startswith('pat_'):
            self.show_error("Token 格式错误，应以 'pat_' 开头")
            return
            
        # 验证 Bot ID 格式
        if not coze_bot_id.isdigit():
            self.show_error("Bot ID 应为纯数字")
            return
            
        # 直接保存配置
        self.save_config(coze_token, coze_bot_id)
        
    def on_reset_clicked(self):
        """重置按钮点击事件"""
        self.load_config()
        self.status_label.setText("配置已重置")
        self.status_label.setStyleSheet("color: #666; padding: 10px;")
        
        InfoBar.info(
            title='配置重置',
            content='配置已重置为保存的值',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
        
    def save_config(self, coze_token, coze_bot_id):
        """保存配置"""
        try:
            self.logger.info("开始保存配置...")
            
            # 禁用按钮
            self.save_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            
            # 更新状态
            self.status_label.setText("正在保存配置...")
            self.status_label.setStyleSheet("color: #1890ff; padding: 10px;")
            
            # 使用配置管理器保存配置
            self.config_manager.coze_token = coze_token
            self.config_manager.coze_bot_id = coze_bot_id
            
            # 保存到文件
            success = self.config_manager.save_config()
            
            if success:
                self.logger.info("配置保存成功")
                self.status_label.setText("配置保存成功！")
                self.status_label.setStyleSheet("color: #52c41a; padding: 10px;")
                
                InfoBar.success(
                    title='保存成功',
                    content='配置已成功保存到系统',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                self.show_error("配置保存失败")
                
        except Exception as e:
            self.logger.error(f"保存配置异常: {e}")
            self.show_error(f"保存失败: {str(e)}")
            
        finally:
            # 恢复按钮状态
            self.save_button.setEnabled(True)
            self.reset_button.setEnabled(True)
        
    def show_error(self, message):
        """显示错误信息"""
        self.status_label.setText(f"错误: {message}")
        self.status_label.setStyleSheet("color: #ff4d4f; padding: 10px;")
        
        InfoBar.error(
            title='配置错误',
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self
        )
        
    def closeEvent(self, event):
        """关闭事件"""
        super().closeEvent(event)
