from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (TextEdit, PrimaryPushButton, PushButton,
                          FluentIcon, InfoBar, InfoBarPosition)
import threading
import asyncio
import traceback
from PDD.pdd_app import PDDApp
from utils.logger import get_logger, get_log_queue


class MonitorThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, stop_event, account_name=None):
        super().__init__()
        self.stop_event = stop_event
        self.account_name = account_name  # 新增账号名参数
        
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            app = PDDApp(self.account_name, self.stop_event)  # 传递stop_event
            loop.run_until_complete(app.start())
        except Exception as e:
            self.error.emit(str(e))
            traceback.print_exc()
        finally:
            self.finished.emit()


class MonitorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('monitorView')
        self.logger = get_logger('monitor')
        self.log_queue = get_log_queue()
        self.monitoring = False
        self.stop_event = threading.Event()
        self.monitor_thread = None
        
        self.initUI()
        self.start_log_listener()
        
    def initUI(self):
        self.output_text = TextEdit(self)
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("监控日志将在此显示...")
        
        # 创建按钮
        self.start_button = PrimaryPushButton('开始监控', self, icon=FluentIcon.PLAY)
        self.stop_button = PushButton('停止监控', self, icon=FluentIcon.PAUSE)
        self.clear_button = PushButton('清空输出', self, icon=FluentIcon.DELETE)
        
        self.stop_button.setEnabled(False)
        
        # 连接信号
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.clear_button.clicked.connect(self.clear_output)
        
        # 布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.output_text)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def start_log_listener(self):
        # 创建定时器检查日志队列
        self.timer = self.startTimer(100)
        
    def timerEvent(self, event):
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self.update_output(message)
            
    def start_monitoring(self):
        if not self.monitoring:
            self.logger.info("开始监控...")
            self.monitoring = True
            self.stop_event.clear()
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # TODO: 这里请填写实际账号名
            account_name = "请填写账号名"
            self.monitor_thread = MonitorThread(self.stop_event, account_name=account_name)
            self.monitor_thread.finished.connect(self.on_monitoring_finished)
            self.monitor_thread.error.connect(self.on_monitoring_error)
            self.monitor_thread.start()
            
            InfoBar.success(
                title='监控已启动',
                content='系统开始监控消息',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
    def stop_monitoring(self):
        if self.monitoring:
            self.stop_event.set()
            self.logger.info("正在停止监控，请稍候...")
            
            InfoBar.warning(
                title='正在停止',
                content='正在安全停止监控...',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
            # 启动超时检查定时器
            self.stop_timer = QTimer()
            self.stop_timer.setSingleShot(True)
            self.stop_timer.timeout.connect(self.force_stop)
            self.stop_timer.start(10000)  # 10秒超时
            
    def force_stop(self):
        """强制停止监控（超时后调用）"""
        if self.monitoring:
            self.logger.warning("监控停止超时，强制重置状态")
            self.monitoring = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            # 如果线程还在运行，尝试终止它
            if self.monitor_thread and self.monitor_thread.isRunning():
                self.monitor_thread.terminate()
                self.monitor_thread.wait(1000)  # 等待1秒
                
            InfoBar.warning(
                title='监控已强制停止',
                content='监控已超时强制停止',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
    def on_monitoring_finished(self):
        self.monitoring = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.logger.info("监控已完全停止")
        
        # 取消超时定时器
        if hasattr(self, 'stop_timer'):
            self.stop_timer.stop()
        
        InfoBar.success(
            title='监控已停止',
            content='监控已安全停止',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
    def on_monitoring_error(self, error_msg):
        InfoBar.error(
            title='监控错误',
            content=f'发生错误: {error_msg}',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        
    def clear_output(self):
        self.output_text.clear()
        
    def update_output(self, message):
        self.output_text.append(message)
        # 滚动到底部
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum()) 