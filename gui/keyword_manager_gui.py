import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import os

class KeywordManagerGUI:
    def __init__(self, notebook, logger):
        self.frame = ttk.Frame(notebook)
        self.logger = logger
        self.keywords = []
        self.regex_patterns = []
        self.create_widgets()
        self.load_keywords()

    def create_widgets(self):
        keyword_frame = ttk.LabelFrame(self.frame, text="人工服务关键词", padding=(10, 50))
        keyword_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        ttk.Label(keyword_frame, text="关键词:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.keyword_text = scrolledtext.ScrolledText(keyword_frame, wrap=tk.WORD, width=30, height=30)
        self.keyword_text.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        regex_frame = ttk.LabelFrame(self.frame, text="正则表达式模式", padding=(10, 50))
        regex_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        ttk.Label(regex_frame, text="正则表达式:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.regex_text = scrolledtext.ScrolledText(regex_frame, wrap=tk.WORD, width=30, height=30)
        self.regex_text.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        button_frame = ttk.Frame(self.frame)
        button_frame.pack(side=tk.BOTTOM, padx=10, pady=10, fill=tk.X)

        save_button = ttk.Button(button_frame, text="保存关键词设置", command=self.save_keywords)
        save_button.pack(side=tk.RIGHT, padx=5)

        ttk.Label(button_frame, text="点击保存以更新关键词设置").pack(side=tk.LEFT, padx=5)

    def load_keywords(self):
        try:
            with open('config/keywords.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.keywords = data.get('human_service_keywords', [])
                self.regex_patterns = data.get('regex_patterns', [])
        except FileNotFoundError:
            self.logger.warning("关键词文件未找到，使用默认关键词")
            self.keywords = ['转人工', '人工客服', '人', '客服', '人工']
        except json.JSONDecodeError:
            self.logger.error("关键词文件格式错误，使用默认关键词")
            self.keywords = ['转人工', '人工客服', '人', '客服', '人工']
        
        self.update_text_widgets()

    def update_text_widgets(self):
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

    def generate_regex(self, keyword):
        return f".*{keyword}.*"