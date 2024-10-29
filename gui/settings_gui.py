import tkinter as tk
from tkinter import ttk
from PDD.Set_up_online import set_csstatus

class SettingsGUI:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        self.create_widgets()

    def create_widgets(self):
        status_frame = ttk.LabelFrame(self.frame, text="在线状态", padding=(10, 5))
        status_frame.pack(padx=10, pady=10, fill=tk.X)

        self.status_var = tk.StringVar(value="1")
        ttk.Radiobutton(status_frame, text="在线", variable=self.status_var, value="1").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(status_frame, text="忙碌", variable=self.status_var, value="0").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(status_frame, text="离线", variable=self.status_var, value="3").pack(side=tk.LEFT, padx=5)
        ttk.Button(status_frame, text="设置状态", command=self.set_status).pack(side=tk.LEFT, padx=5)

    def set_status(self):
        status = self.status_var.get()
        # 这里需要实现设置状态的逻辑，可能需要调用 account_manager 的方法
        # 例如：self.account_manager.set_all_accounts_status(status)
        print(f"设置所有账号状态为: {status}")  # 临时的打印语句，之后需要替换为实际的逻辑
