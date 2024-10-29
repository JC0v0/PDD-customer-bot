import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import asyncio
from PDD.app import monitor_all_accounts
from utils.logger import get_logger, get_log_queue

class MonitorGUI:
    def __init__(self, notebook, logger, log_queue):
        self.frame = ttk.Frame(notebook)
        self.logger = logger
        self.monitoring = False
        self.stop_event = threading.Event()
        self.monitor_thread = None
        self.log_queue = log_queue

        self.create_widgets()
        self.start_log_listener()

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 输出区域
        self.output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=90, height=35)
        self.output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(padx=10, pady=10)

        self.start_button = ttk.Button(control_frame, text="开始监控", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="停止监控", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(control_frame, text="清空输出", command=self.clear_output)
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def start_log_listener(self):
        self.frame.after(100, self.check_log_queue)

    def check_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self.update_output(message)
        self.frame.after(100, self.check_log_queue)

    def start_monitoring(self):
        if not self.monitoring:
            self.logger.info("开始监控...")
            self.monitoring = True
            self.stop_event.clear()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.monitor_thread = threading.Thread(target=self.run_monitor, daemon=True)
            self.monitor_thread.start()

    def run_monitor(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_monitor())
        except Exception as e:
            self.logger.error(f"监控过程中发生错误: {str(e)}")
            import traceback
            self.logger.error(f"错误详情:\n{traceback.format_exc()}")
        finally:
            self.monitoring = False
            self.frame.after(0, self.update_buttons)

    async def async_monitor(self):
        try:
            await monitor_all_accounts(self.stop_event)
        except Exception as e:
            self.logger.error(f"监控过程中发生错误: {str(e)}")
            import traceback
            self.logger.error(f"错误详情:\n{traceback.format_exc()}")

    def stop_monitoring(self):
        if self.monitoring:
            self.stop_event.set()
            self.logger.info("正在停止监控，稍候...")
            if self.monitor_thread:
                self.monitor_thread.join(timeout=3)
            self.monitoring = False
            self.update_buttons()
            self.logger.info("监控已完全停止")

    def update_buttons(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def update_output(self, message):
        self.frame.after(0, self._update_output, message)

    def _update_output(self, message):
        self.output_text.insert(tk.END, message + '\n')
        self.output_text.see(tk.END)
