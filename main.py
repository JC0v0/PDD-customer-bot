import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import asyncio
import threading
import queue
import json
from datetime import datetime, timedelta, timezone
from PDD.account_manager import AccountManager
from PDD.app import monitor_all_accounts, AccountMonitor
from PDD.review_manager import PddReviewManager
from PDD.Set_up_online import set_csstatus
from logger import get_logger, get_log_queue

class PinduoduoCustomerServiceGUI:
    def __init__(self, master):
        self.master = master
        master.title("拼多多客服系统")
        master.geometry("1200x800")

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.account_manager = AccountManager()
        self.account_monitors = {}

        self.keywords, self.regex_patterns = self.load_keywords()

        self.create_widgets()
        self.process = None
        self.monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()

        self.logger = get_logger('main')
        self.log_queue = get_log_queue()

        self.message_thread = threading.Thread(target=self.process_messages, daemon=True)
        self.message_thread.start()

        self.review_manager = PddReviewManager()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.account_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.account_frame, text="账号管理")
        self.create_account_widgets()

        self.monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_frame, text="消息监控")
        self.create_monitor_widgets()

        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="设置")
        self.create_settings_widgets()

        self.keyword_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.keyword_frame, text="关键词设置")
        self.create_keyword_widgets()

        self.review_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.review_frame, text="评论管理")
        self.create_review_widgets()

    def create_account_widgets(self):
        tree_frame = ttk.Frame(self.account_frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.account_tree = ttk.Treeview(tree_frame, columns=('Name', 'Expiry'), show='headings', yscrollcommand=tree_scroll.set)
        self.account_tree.heading('Name', text='账号名称')
        self.account_tree.heading('Expiry', text='过期时间')
        self.account_tree.column('Name', width=150)
        self.account_tree.column('Expiry', width=150)
        self.account_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree_scroll.config(command=self.account_tree.yview)

        button_frame = ttk.Frame(self.account_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        ttk.Button(button_frame, text="添加账号", command=self.add_account).pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="批量添加账号", command=self.batch_add_accounts).pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="删除账号", command=self.remove_account).pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="刷新列表", command=self.update_account_list).pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="重新获取Cookies", command=self.refresh_selected_account_cookies).pack(fill=tk.X, pady=5)

    def create_monitor_widgets(self):
        self.output_text = scrolledtext.ScrolledText(self.monitor_frame, wrap=tk.WORD, width=120, height=35)
        self.output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.monitor_frame)
        control_frame.pack(padx=10, pady=10)

        self.start_button = ttk.Button(control_frame, text="开始监控", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="停止监控", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(control_frame, text="清空输出", command=self.clear_output)
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def create_settings_widgets(self):
        status_frame = ttk.LabelFrame(self.settings_frame, text="在线状态", padding=(10, 5))
        status_frame.pack(padx=10, pady=10, fill=tk.X)

        self.status_var = tk.StringVar(value="1")
        ttk.Radiobutton(status_frame, text="在线", variable=self.status_var, value="1").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(status_frame, text="忙碌", variable=self.status_var, value="0").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(status_frame, text="离线", variable=self.status_var, value="3").pack(side=tk.LEFT, padx=5)

        ttk.Button(status_frame, text="设置状态", command=self.set_status).pack(side=tk.LEFT, padx=5)

    def create_keyword_widgets(self):
        keyword_frame = ttk.LabelFrame(self.keyword_frame, text="人工服务关键词", padding=(10, 5))
        keyword_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.keyword_text = scrolledtext.ScrolledText(keyword_frame, wrap=tk.WORD, width=40, height=20)
        self.keyword_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        regex_frame = ttk.LabelFrame(self.keyword_frame, text="正则表达式模式", padding=(10, 5))
        regex_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.regex_text = scrolledtext.ScrolledText(regex_frame, wrap=tk.WORD, width=40, height=20)
        self.regex_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(self.keyword_frame)
        button_frame.pack(side=tk.BOTTOM, padx=10, pady=10, fill=tk.X)

        save_button = ttk.Button(button_frame, text="保存关键词设置", command=self.save_keywords)
        save_button.pack(side=tk.RIGHT, padx=5)

        self.load_keywords_to_ui()

    def create_review_widgets(self):
        date_frame = ttk.Frame(self.review_frame)
        date_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(date_frame, text="开始日期:").pack(side=tk.LEFT, padx=(0, 5))
        self.start_date_entry = ttk.Entry(date_frame, width=20)
        self.start_date_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))

        ttk.Label(date_frame, text="结束日期:").pack(side=tk.LEFT, padx=(0, 5))
        self.end_date_entry = ttk.Entry(date_frame, width=20)
        self.end_date_entry.pack(side=tk.LEFT)
        self.end_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        button_frame = ttk.Frame(self.review_frame)
        button_frame.pack(pady=10)

        self.fetch_reviews_button = ttk.Button(button_frame, text="获取评论", command=self.fetch_reviews)
        self.fetch_reviews_button.pack(side=tk.LEFT, padx=5)

        self.stop_fetch_reviews_button = ttk.Button(button_frame, text="停止获取", command=self.stop_fetch_reviews, state=tk.DISABLED)
        self.stop_fetch_reviews_button.pack(side=tk.LEFT, padx=5)

        self.auto_reply_button = ttk.Button(button_frame, text="自动回复", command=self.auto_reply_reviews)
        self.auto_reply_button.pack(side=tk.LEFT, padx=5)

        self.stop_auto_reply_button = ttk.Button(button_frame, text="停止回复", command=self.stop_auto_reply, state=tk.DISABLED)
        self.stop_auto_reply_button.pack(side=tk.LEFT, padx=5)

        self.review_output = scrolledtext.ScrolledText(self.review_frame, wrap=tk.WORD, width=80, height=20)
        self.review_output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.create_custom_reply_widgets()

    def create_custom_reply_widgets(self):
        custom_reply_frame = ttk.LabelFrame(self.review_frame, text="自定义回复话术", padding=(10, 5))
        custom_reply_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(custom_reply_frame, text="5星评价回复:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.reply_5_star = scrolledtext.ScrolledText(custom_reply_frame, wrap=tk.WORD, width=100, height=3)
        self.reply_5_star.grid(row=0, column=1, padx=5, pady=5)
        self.reply_5_star.insert(tk.END, "非常感谢您的好评和支持！我们很高兴知道您对我们的产品感到满意。您的满意是我们最大的动力，期待您再次光临。")

        ttk.Label(custom_reply_frame, text="4星评价回复:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.reply_4_star = scrolledtext.ScrolledText(custom_reply_frame, wrap=tk.WORD, width=100, height=3)
        self.reply_4_star.grid(row=1, column=1, padx=5, pady=5)
        self.reply_4_star.insert(tk.END, "感谢您的评价和支持。我们期待您再次体验我们的产品或服务，希望下次能给您带来完全的满意。")

        ttk.Label(custom_reply_frame, text="3星及以下评价回复:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.reply_3_star = scrolledtext.ScrolledText(custom_reply_frame, wrap=tk.WORD, width=100, height=3)
        self.reply_3_star.grid(row=2, column=1, padx=5, pady=5)
        self.reply_3_star.insert(tk.END, "我们感谢您诚实的评价。为了更好地理解并改进，我们非常欢迎您与我们沟通，分享您的看法和建议。")

        button_frame = ttk.Frame(custom_reply_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        save_button = ttk.Button(button_frame, text="保存回复话术", command=self.save_custom_replies)
        save_button.pack()

    def update_account_list(self):
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        for account_name, account_data in self.account_manager.accounts.items():
            expiry_date_str = account_data.get('expiry_date', '')
            if expiry_date_str:
                try:
                    expiry_date = datetime.fromisoformat(expiry_date_str)
                    if expiry_date.tzinfo is None:
                        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                except ValueError:
                    expiry_date = datetime.min.replace(tzinfo=timezone.utc)
            else:
                expiry_date = datetime.min.replace(tzinfo=timezone.utc)
            
            self.account_tree.insert('', 'end', values=(account_name, expiry_date.strftime("%Y-%m-%d %H:%M:%S")))

    def add_account(self):
        account_name = simpledialog.askstring("添加账号", "请输入新账号名称：")
        if account_name:
            asyncio.run(self.async_add_account(account_name))

    async def async_add_account(self, account_name):
        success = await self.account_manager.add_account(account_name)
        if success:
            self.logger.info(f"账号 {account_name} 添加成功")
            self.update_account_list()
        else:
            self.logger.error(f"添加账号 {account_name} 失败")

    def batch_add_accounts(self):
        account_names = simpledialog.askstring("批量添加账号", "请输入要批量添加的账号名称，用逗号分隔：")
        if account_names:
            asyncio.run(self.async_batch_add_accounts(account_names.split(',')))

    async def async_batch_add_accounts(self, account_names):
        results = await self.account_manager.batch_add_accounts(account_names)
        success_count = sum(results.values())
        fail_count = len(results) - success_count
        self.logger.info(f"批量添加结果 - 成功: {success_count}, 失败: {fail_count}")
        self.update_account_list()

    def remove_account(self):
        selected = self.account_tree.selection()
        if selected:
            account_name = self.account_tree.item(selected[0])['values'][0]
            if messagebox.askyesno("确认", f"确定要删除账号 {account_name} 吗？"):
                asyncio.run(self.async_remove_account(account_name))
        else:
            self.logger.warning("请先选择要删除的账号")

    async def async_remove_account(self, account_name):
        success = await self.account_manager.remove_account(account_name)
        if success:
            self.logger.info(f"账号 {account_name} 删除成功")
            self.update_account_list()
        else:
            self.logger.error(f"删除账号 {account_name} 失败")

    def refresh_selected_account_cookies(self):
        selected = self.account_tree.selection()
        if not selected:
            self.logger.warning("请先选择要刷新Cookies的账号")
            return
        
        account_name = self.account_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("确认", f"确定要重新获取账号 {account_name} 的Cookies吗？"):
            threading.Thread(target=self.async_refresh_cookies, args=(account_name,), daemon=True).start()

    def async_refresh_cookies(self, account_name):
        success = asyncio.run(self.account_manager.auto_login(account_name))
        if success:
            self.logger.info(f"账号 {account_name} 的Cookies已成功刷新")
        else:
            self.logger.error(f"账号 {account_name} 的Cookies刷新失败")
        self.master.after(0, self.update_account_list)

    def start_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.stop_event.clear()
            self.output_text.delete(1.0, tk.END)
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            self.monitor_thread = threading.Thread(target=self.run_monitor, daemon=True)
            self.monitor_thread.start()

    def run_monitor(self):
        try:
            monitor_all_accounts(self.stop_event)
        except Exception as e:
            self.logger.error(f"监控过程中发生错误: {str(e)}")
        finally:
            self.monitoring = False
            self.master.after(0, self.update_buttons)

    def stop_monitoring(self):
        if self.monitoring:
            self.stop_event.set()
            self.logger.info("正在停止监控，请稍候...")
            if self.monitor_thread:
                self.monitor_thread.join(timeout=10)
            self.monitoring = False
            self.update_buttons()
            self.logger.info("监控已完全停止")

    def update_buttons(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def update_output(self, message):
        self.output_text.insert(tk.END, message + '\n')
        self.output_text.see(tk.END)

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def set_status(self):
        status = self.status_var.get()
        success_count = 0
        fail_count = 0
        for account_name, account_data in self.account_manager.accounts.items():
            result = set_csstatus(account_name, account_data, status)
            if result and result.get('success'):
                success_count += 1
                self.logger.info(f"账号 {account_name} 状态设置成功: {status}")
            else:
                fail_count += 1
                self.logger.error(f"账号 {account_name} 状态设置失败")
        
        message = f"状态设置完成。\n成功: {success_count}\n失败: {fail_count}"
        self.logger.info(message)

    def load_keywords(self):
        try:
            with open('config/keywords.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('human_service_keywords', []), data.get('regex_patterns', [])
        except FileNotFoundError:
            self.logger.warning("关键词文件未找到，使用默认关键词")
            return ['转人工', '人工客服', '真人', '客服', '人工'], []
        except json.JSONDecodeError:
            self.logger.error("关键词文件格式错误，使用默认关键词")
            return ['转人工', '人工客服', '真人', '客服', '人工'], []

    def load_keywords_to_ui(self):
        self.keyword_text.delete(1.0, tk.END)
        self.regex_text.delete(1.0, tk.END)

        for keyword in self.keywords:
            self.keyword_text.insert(tk.END, keyword + '\n')
        
        for pattern in self.regex_patterns:
            self.regex_text.insert(tk.END, pattern + '\n')

    def save_keywords(self):
        keywords = self.keyword_text.get(1.0, tk.END).strip().split('\n')
        regex_patterns = self.regex_text.get(1.0, tk.END).strip().split('\n')

        keywords = [k.strip() for k in keywords if k.strip()]
        regex_patterns = [r.strip() for r in regex_patterns if r.strip()]

        data = {
            'human_service_keywords': keywords,
            'regex_patterns': regex_patterns
        }

        try:
            with open('config/keywords.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info("关键词设置已保存")
            self.keywords, self.regex_patterns = keywords, regex_patterns
        except Exception as e:
            self.logger.error(f"保存关键词设置时出错：{str(e)}")

    def fetch_reviews(self):
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        
        try:
            start_time = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()) + 86399  # 加上一天减1秒
        except ValueError:
            self.logger.error("日期格式错误，请使用 YYYY-MM-DD 格式")
            return

        selected = self.account_tree.selection()
        if not selected:
            self.logger.warning("请先选择一个账号")
            return
        
        account_name = self.account_tree.item(selected[0])['values'][0]
        account_cookies = self.account_manager.get_account_cookies(account_name)
        if not account_cookies:
            self.logger.error(f"无法获取账号 {account_name} 的 cookies")
            return

        self.review_manager.set_cookie('; '.join([f"{k}={v}" for k, v in account_cookies.items()]))
        
        def process_reviews_thread():
            self.review_manager.stop_fetching = False
            self.review_manager.fetch_reviews(start_time, end_time, self.update_review_output)
            self.master.after(0, self.update_review_buttons)

        self.review_output.delete(1.0, tk.END)  # 清空之前的输出
        threading.Thread(target=process_reviews_thread, daemon=True).start()
        self.logger.info("开始获取评论...")
        self.fetch_reviews_button.config(state=tk.DISABLED)
        self.stop_fetch_reviews_button.config(state=tk.NORMAL)

    def stop_fetch_reviews(self):
        self.review_manager.stop_fetching = True
        self.logger.info("正在停止获取评论...")
        self.fetch_reviews_button.config(state=tk.NORMAL)
        self.stop_fetch_reviews_button.config(state=tk.DISABLED)

    def auto_reply_reviews(self):
        def auto_reply_thread():
            self.review_manager.stop_replying = False
            self.review_manager.auto_reply_reviews(self.update_review_output)
            self.master.after(0, self.update_auto_reply_buttons)

        threading.Thread(target=auto_reply_thread, daemon=True).start()
        self.logger.info("开始自动回复评论...")
        self.auto_reply_button.config(state=tk.DISABLED)
        self.stop_auto_reply_button.config(state=tk.NORMAL)

    def stop_auto_reply(self):
        self.review_manager.stop_replying = True
        self.logger.info("正在停止自动回复...")
        self.auto_reply_button.config(state=tk.NORMAL)
        self.stop_auto_reply_button.config(state=tk.DISABLED)

    def update_review_output(self, message):
        self.master.after(0, lambda: self.review_output.insert(tk.END, message + '\n'))
        self.master.after(0, self.review_output.see, tk.END)

    def update_review_buttons(self):
        self.fetch_reviews_button.config(state=tk.NORMAL)
        self.stop_fetch_reviews_button.config(state=tk.DISABLED)

    def update_auto_reply_buttons(self):
        self.auto_reply_button.config(state=tk.NORMAL)
        self.stop_auto_reply_button.config(state=tk.DISABLED)

    def save_custom_replies(self):
        custom_replies = {
            5: self.reply_5_star.get("1.0", tk.END).strip(),
            4: self.reply_4_star.get("1.0", tk.END).strip(),
            3: self.reply_3_star.get("1.0", tk.END).strip()
        }
        self.review_manager.set_custom_replies(custom_replies)
        self.logger.info("自定义回复话术已保存")

    def process_messages(self):
        while True:
            try:
                message = self.log_queue.get(timeout=1)
                self.master.after(0, self.update_output, message)
            except queue.Empty:
                continue

if __name__ == "__main__":
    root = tk.Tk()
    app = PinduoduoCustomerServiceGUI(root)
    root.mainloop()