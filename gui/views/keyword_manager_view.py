from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import (CardWidget, TextEdit, PrimaryPushButton,
                          InfoBar, InfoBarPosition, FluentIcon)
import json
import os
from utils.logger import get_logger
from PDD.keyword_transfer import KeywordTransfer


class KeywordManagerView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('keywordManagerView')
        self.logger = get_logger('keyword_manager')
        self.keyword_transfer = KeywordTransfer()
        self.keywords = []
        self.regex_patterns = []
        
        self.initUI()
        self.load_keywords()
        
    def initUI(self):
        main_layout = QHBoxLayout(self)
        
        # 关键词卡片
        keyword_card = CardWidget(self)
        keyword_layout = QVBoxLayout(keyword_card)
        
        keyword_label = QLabel('人工服务关键词', self)
        keyword_label.setStyleSheet('font-size: 16px; font-weight: bold; margin-bottom: 10px;')
        
        self.keyword_text = TextEdit(self)
        self.keyword_text.setPlaceholderText("每行输入一个关键词...")
        
        keyword_layout.addWidget(keyword_label)
        keyword_layout.addWidget(self.keyword_text)
        keyword_card.setLayout(keyword_layout)
        
        # 正则表达式卡片
        regex_card = CardWidget(self)
        regex_layout = QVBoxLayout(regex_card)
        
        regex_label = QLabel('正则表达式模式', self)
        regex_label.setStyleSheet('font-size: 16px; font-weight: bold; margin-bottom: 10px;')
        
        self.regex_text = TextEdit(self)
        self.regex_text.setPlaceholderText("每行输入一个正则表达式...")
        
        regex_layout.addWidget(regex_label)
        regex_layout.addWidget(self.regex_text)
        regex_card.setLayout(regex_layout)
        
        # 保存按钮
        button_layout = QVBoxLayout()
        self.save_button = PrimaryPushButton('保存关键词设置', self, icon=FluentIcon.SAVE)
        self.save_button.clicked.connect(self.save_keywords)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(keyword_card, stretch=1)
        main_layout.addWidget(regex_card, stretch=1)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def load_keywords(self):
        # 从KeywordTransfer获取关键词和正则表达式
        self.keywords, compiled_patterns = self.keyword_transfer.load_keywords()
        # 将编译后的正则表达式模式转换回字符串形式
        self.regex_patterns = [pattern.pattern for pattern in compiled_patterns]
        self.update_text_widgets()
        
    def update_text_widgets(self):
        self.keyword_text.clear()
        self.regex_text.clear()
        
        self.keyword_text.setPlainText('\n'.join(self.keywords))
        self.regex_text.setPlainText('\n'.join(self.regex_patterns))
        
    def save_keywords(self):
        keywords = self.keyword_text.toPlainText().strip().split('\n')
        regex_patterns = self.regex_text.toPlainText().strip().split('\n')
        
        keywords = [k.strip() for k in keywords if k.strip()]
        regex_patterns = [r.strip() for r in regex_patterns if r.strip()]
        
        # 验证正则表达式的有效性
        invalid_patterns = []
        for pattern in regex_patterns:
            try:
                import re
                re.compile(pattern)
            except re.error:
                invalid_patterns.append(pattern)
        
        if invalid_patterns:
            # 如果有无效的正则表达式，显示错误信息
            error_msg = "以下正则表达式无效：\n" + "\n".join(invalid_patterns)
            InfoBar.error(
                title='保存失败',
                content=error_msg,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return
        
        # 使用KeywordTransfer保存关键词
        success = self.keyword_transfer.save_keywords(keywords, regex_patterns)
        
        if success:
            self.keywords = keywords
            self.regex_patterns = regex_patterns
            
            InfoBar.success(
                title='保存成功',
                content='关键词设置已成功保存',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title='保存失败',
                content='保存关键词设置时出错',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            ) 