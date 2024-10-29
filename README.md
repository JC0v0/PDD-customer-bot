# 拼多多客服系统

## 项目简介

拼多多客服系统是一个综合性的客户服务管理工具,专为拼多多商家设计。本系统旨在提高客服效率,实现部分自动化,同时保留人工介入的灵活性。它适合需要管理多个拼多多店铺客服的商家使用。

## 主要功能

1. **账号管理**
   - 添加、删除、账号
   - 自动登录获取cookies
   - 管理账号cookies的有效期
![image](https://github.com/user-attachments/assets/272c7106-5788-4b7d-bbc5-b4b87c48a2e7)


2. **消息监控**
   - 监控多个账号的未读消息
   - 自动回复客户消息
   - 使用AI (Coze API) 生成回复内容

3. **人工转接**
   - 根据关键词识别需要人工服务的对话
   - 自动将对话转接给在线客服
![d35f6c048e394f89b32e6a6c56c4391](https://github.com/user-attachments/assets/ad770de9-f99d-4622-8f19-13845a699d6d)

4. **评论管理**
   - 获取指定日期范围内的商品评论
   - 自动回复评论
   - 支持自定义评论回复话术
![image](https://github.com/user-attachments/assets/5c9a7bf7-7c0c-4d02-873a-5d6d8b097ed3)

6. **关键词设置**
   - 管理触发人工服务的关键词和正则表达式
![image](https://github.com/user-attachments/assets/a0fbac59-c724-4d5c-a320-c4bc53cf6605)

7. **图形用户界面**
   - 使用tkinter构建的多标签页界面
   - 实时显示监控和操作日志

8. **多线程处理**
   - 使用线程池管理多个账号的并发监控
   - 后台处理不影响GUI响应

9. **数据持久化**
   - 将账号信息、cookies等数据保存到JSON文件
   - 将评论数据导出到CSV文件

10. **安全性考虑**
    - 使用selenium-stealth避免被检测为自动化工具
    - 管理cookies有效期,定期刷新

## 系统要求

- Python 3.7+
- Chrome浏览器 (用于Selenium自动化)

## 安装步骤

1. 克隆仓库到本地:
```git clone https://github.com/JC0v0/PDD-customer-bot.git
```
2. 进入项目目录:
```cd pdd-customer-service
```
3. 安装所需依赖:
```
pip install -r requirements.txt
```
4. 下载与您Chrome浏览器版本匹配的ChromeDriver,并将其放置在`chromedriver-win64`目录下。

## 使用方法

1. 运行主程序
   运行 ‘拼多多客服系统.exe’或者命令行输入：
```
python main.py
```

3. 在图形界面中添加您的拼多多商家账号。

4. 设置自动回复关键词和评论回复话术。

5. 开始监控消息和管理评论。

6. 在config.py文件中设置你的Coze API
```
coze_token = "pat_bUk***************"
coze_bot_id = "73*************"
```
## 注意事项

- 请确保您有权限使用此工具管理相关的拼多多商家账号。
- 使用AI自动回复功能时,请遵守相关的服务条款和法规。
- 定期检查和更新cookies,以确保系统正常运行。

## 贡献指南

欢迎提交问题报告和功能请求。如果您想贡献代码,请先开issue讨论您想要改变的内容。

## 许可证

本项目采用 MIT 许可证 - 详情请见 [LICENSE](LICENSE) 文件。

## 联系方式

如有任何问题或建议,请通过 [issues](https://github.com/your-username/pdd-customer-service/issues) 页面与我们联系。
