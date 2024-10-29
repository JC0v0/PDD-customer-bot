import tkinter as tk
from tkinter import ttk
from gui.account_manager_gui import AccountManagerGUI
from gui.monitor_gui import MonitorGUI
from gui.settings_gui import SettingsGUI
from gui.keyword_manager_gui import KeywordManagerGUI
from utils.icon_loader import IconLoader
from utils.logger import get_logger, get_log_queue
from PDD.account_manager import AccountManager

class PinduoduoCustomerServiceGUI:
    def __init__(self, master):
        self.master = master
        master.title("拼多多客服系统")
        master.geometry("1200x800")

        self.logger = get_logger('main')
        self.log_queue = get_log_queue()
        self.account_manager = AccountManager()
        self.icon_loader = IconLoader()

        self.setup_styles()
        self.create_notebook()
        self.create_gui_components()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

    def create_notebook(self):
        self.notebook = ttk.Notebook(self.master, style='TNotebook')
        self.notebook.pack(expand=True, fill="both", padx=20, pady=20)

    def create_gui_components(self):
        self.account_manager_gui = AccountManagerGUI(self.notebook, self.account_manager, self.icon_loader, self.logger)
        self.monitor_gui = MonitorGUI(self.notebook, self.logger, self.log_queue)  # 修改这行，传递 self.log_queue
        self.settings_gui = SettingsGUI(self.notebook)
        self.keyword_manager_gui = KeywordManagerGUI(self.notebook, self.logger)


        self.notebook.add(self.account_manager_gui.frame, text="账号管理")
        self.notebook.add(self.monitor_gui.frame, text="消息监控")
        self.notebook.add(self.settings_gui.frame, text="设置")
        self.notebook.add(self.keyword_manager_gui.frame, text="关键词设置")


if __name__ == "__main__":
    root = tk.Tk()
    app = PinduoduoCustomerServiceGUI(root)
    root.mainloop()
