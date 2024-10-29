import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import asyncio
import threading
from datetime import datetime, timezone
from PDD.Set_up_online import set_csstatus

class AccountInputDialog(simpledialog.Dialog):
    def body(self, master):
        ttk.Label(master, text="账号名称:").grid(row=0, column=0, sticky="e")
        ttk.Label(master, text="账号密码:").grid(row=1, column=0, sticky="e")
        
        self.account_entry = ttk.Entry(master)
        self.password_entry = ttk.Entry(master, show="*")
        
        self.account_entry.grid(row=0, column=1)
        self.password_entry.grid(row=1, column=1)
        return self.account_entry  # 初始焦点

    def apply(self):
        self.result = (self.account_entry.get(), self.password_entry.get())

class AccountEditDialog(simpledialog.Dialog):
    def __init__(self, parent, title, account_name, password):
        self.account_name = account_name
        self.password = password
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="账号名称:").grid(row=0, column=0, sticky="e")
        ttk.Label(master, text="账号密码:").grid(row=1, column=0, sticky="e")
        
        self.account_entry = ttk.Entry(master)
        self.password_entry = ttk.Entry(master, show="*")
        
        self.account_entry.grid(row=0, column=1)
        self.password_entry.grid(row=1, column=1)
        
        self.account_entry.insert(0, self.account_name)
        self.password_entry.insert(0, self.password)
        
        return self.account_entry

    def apply(self):
        self.result = (self.account_entry.get(), self.password_entry.get())

class AccountManagerGUI:
    def __init__(self, notebook, account_manager, icon_loader, logger):
        self.frame = ttk.Frame(notebook)
        self.account_manager = account_manager
        self.icon_loader = icon_loader
        self.logger = logger

        self.create_widgets()

    def create_widgets(self):
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.account_tree = ttk.Treeview(tree_frame, columns=('Name', 'Expiry', 'Status'), 
                                        show='headings', style='Treeview', selectmode='extended')
        self.account_tree.heading('Name', text='账号名称')
        self.account_tree.heading('Expiry', text='过期时间')
        self.account_tree.heading('Status', text='在线状态')
        self.account_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        self.context_menu = tk.Menu(self.frame, tearoff=0)
        self.context_menu.add_command(label="设置为在线", command=lambda: self.set_account_status("在线"))
        self.context_menu.add_command(label="设置为忙碌", command=lambda: self.set_account_status("忙碌"))
        self.context_menu.add_command(label="设置为离线", command=lambda: self.set_account_status("离线"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="修改账号信息", command=self.edit_account)

        if self.frame.winfo_toplevel().tk.call('tk', 'windowingsystem') == 'aqua':
            self.account_tree.bind("<Button-2>", self.show_context_menu)
        else:
            self.account_tree.bind("<Button-3>", self.show_context_menu)

        button_frame = ttk.Frame(self.frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)

        ttk.Button(button_frame, text=" 添加账号", image=self.icon_loader.add_icon, 
                   compound=tk.LEFT, command=self.add_account, style='LeftIcon.TButton').pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text=" 删除账号", image=self.icon_loader.remove_icon, 
                   compound=tk.LEFT, command=self.remove_account, style='LeftIcon.TButton').pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text=" 刷新列表", image=self.icon_loader.refresh_icon, 
                   compound=tk.LEFT, command=self.update_account_list, style='LeftIcon.TButton').pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text=" 重新获取Cookies", image=self.icon_loader.refresh_icon, 
                   compound=tk.LEFT, command=self.refresh_selected_account_cookies, style='LeftIcon.TButton').pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(self.frame, text="", foreground="red")
        self.status_label.pack(pady=5)

        self.update_account_list()

    def show_context_menu(self, event):
        item = self.account_tree.identify_row(event.y)
        if item:
            if item not in self.account_tree.selection():
                self.account_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def set_account_status(self, status):
        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择账号")
            return

        success_count = 0
        fail_count = 0
        
        for item in selected:
            account_name = self.account_tree.item(item)['values'][0]
            account_data = self.account_manager.accounts.get(account_name)
            
            if account_data:
                result = set_csstatus(account_name, account_data, status)
                if result and result.get('success'):
                    success_message = f"账号 {account_name} 状态设置成功: {status}"
                    self.logger.info(success_message)
                    self.account_manager.accounts[account_name]['status'] = status
                    success_count += 1
                else:
                    error_message = f"账号 {account_name} 状态设置失败"
                    self.logger.error(error_message)
                    fail_count += 1
            else:
                warning_message = f"未找到账号数据: {account_name}"
                self.logger.warning(warning_message)
                fail_count += 1

        # 更新账号列表
        self.update_account_list()
        
        # 显示操作结果
        result_message = f"操作完成\n成功: {success_count} 个\n失败: {fail_count} 个"
        if fail_count > 0:
            messagebox.showwarning("操作结果", result_message)
        else:
            messagebox.showinfo("操作结果", result_message)

    def add_account(self):
        dialog = AccountInputDialog(self.frame, title="添加账号")
        if dialog.result:
            account_name, password = dialog.result
            if account_name and password:
                threading.Thread(target=self.async_add_account, args=(account_name, password), daemon=True).start()

    def async_add_account(self, account_name, password):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(self.account_manager.add_account(account_name, password))
        if success:
            self.frame.after(0, self.update_account_list)
        else:
            messagebox.showerror("错误", f"添加账号 {account_name} 失败")

    def remove_account(self):
        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的账号")
            return

        account_name = self.account_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("确认", f"确定要删除账号 {account_name} 吗？"):
            threading.Thread(target=self.async_remove_account, args=(account_name,), daemon=True).start()

    def async_remove_account(self, account_name):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(self.account_manager.remove_account(account_name))
        if success:
            self.frame.after(0, self.update_account_list)
        else:
            messagebox.showerror("错误", f"删除账号 {account_name} 失败")

    def update_account_list(self):
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        for account_name, account_data in self.account_manager.accounts.items():
            expiry_date = account_data.get('expiry_date', '')
            if expiry_date:
                expiry_date = datetime.fromisoformat(expiry_date)
                expiry_date_str = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                expiry_date_str = "未设置"
            status = account_data.get('status', '未设置')
            self.account_tree.insert('', 'end', values=(account_name, expiry_date_str, status))

    def refresh_selected_account_cookies(self):
        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要刷新Cookies的账号")
            return

        account_name = self.account_tree.item(selected[0])['values'][0]
        account_data = self.account_manager.accounts.get(account_name)
        if account_data and 'password' in account_data:
            if messagebox.askyesno("确认", f"确定要重新获取账号 {account_name} 的Cookies吗？"):
                threading.Thread(target=self.async_refresh_cookies, args=(account_name, account_data['password']), daemon=True).start()
        else:
            messagebox.showwarning("警告", f"账号 {account_name} 缺少密码信息")

    def async_refresh_cookies(self, account_name, password):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(self.account_manager.refresh_account_cookies(account_name, password))
        if success:
            self.frame.after(0, self.update_account_list)

    def edit_account(self):
        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要修改的账号")
            return

        account_name = self.account_tree.item(selected[0])['values'][0]
        account_data = self.account_manager.accounts.get(account_name)
        if account_data:
            dialog = AccountEditDialog(self.frame, "修改账号信息", account_name, account_data.get('password', ''))
            if dialog.result:
                new_account_name, new_password = dialog.result
                if new_account_name and new_password:
                    threading.Thread(target=self.async_edit_account, args=(account_name, new_account_name, new_password), daemon=True).start()
        else:
            messagebox.showwarning("警告", f"未找到账号数据: {account_name}")

    def async_edit_account(self, old_account_name, new_account_name, new_password):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(self.account_manager.edit_account(old_account_name, new_account_name, new_password))
        if success:
            self.logger.info(f"账号 {old_account_name} 修改成功")
            self.frame.after(0, self.update_account_list)
        else:
            messagebox.showerror("错误", f"修改账号 {old_account_name} 失败")




