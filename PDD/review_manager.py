import requests
import csv
import time
from datetime import datetime
from config import review_url, reply_url
from logger import get_logger
logger = get_logger('review_manager')

class PddReviewManager:
    def __init__(self):
        self.review_url = review_url
        self.reply_url = reply_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            "Content-Type": "application/json"
        }
        self.csv_filename = '评论信息.csv'
        self.csv_field_names = [
            "评论ID", "用户ID", "商品ID", "订单ID", "商家ID",
            "评分", "描述得分", "物流得分", "服务得分",
            "评论内容", "商品名称", "订单编号", "回复内容", 
            "图片链接", "clientDesc", "desc", "评论时间"
        ]
        self.cookies = {}
        self.stop_fetching = False
        self.stop_replying = False
        self.reviews = []
        self.custom_replies = {
            5: "非常感谢您的好评和支持！我们很高兴知道您对我们的产品感到满意。您的满意是我们最大的动力，期待您再次光临。",
            4: "感谢您的评价和支持。我们期待您再次体验我们的产品或服务，希望下次能给您带来完全的满意。",
            3: "我们感谢您诚实的评价。为了更好地理解并改进，我们非常欢迎您与我们沟通，分享您的看法和建议。"
            }

    def set_cookie(self, cookie):
        self.cookies = {'Cookie': cookie}

    def fetch_reviews(self, start_time, end_time, update_callback):
        page_no = 1
        self.reviews = []
        while not self.stop_fetching:
            response_data = self.fetch_reviews_page(start_time, end_time, page_no)
            if response_data and response_data.get('success') and response_data['errorCode'] == 1000000:
                reviews = response_data.get('result', {}).get('data', [])
                if reviews:
                    self.reviews.extend(reviews)
                    self.save_reviews_to_csv(reviews)
                    update_callback(f"已获取第 {page_no} 页的评论数据，共 {len(reviews)} 条。")
                    page_no += 1
                else:
                    update_callback("没有更多评论数据。")
                    break
            else:
                update_callback("获取评论数据失败。")
                break
            if self.stop_fetching:
                update_callback("用户停止了获取评论。")
                break
            time.sleep(1)  # 控制请求频率，避免过于频繁
        update_callback(f"共获取到 {len(self.reviews)} 条评论。")

    def fetch_reviews_page(self, start_time, end_time, page_no, page_size=40):
        data = {
            "startTime": start_time,
            "endTime": end_time,
            "pageNo": page_no,
            "pageSize": page_size,
            "descScore": ["1", "2", "3", "4", "5"],
            "orderSn": ""
        }
        response = requests.post(self.review_url, headers=self.headers, json=data, cookies=self.cookies)
        return response.json() if response.status_code == 200 else None

    def save_reviews_to_csv(self, reviews):
        with open(self.csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.csv_field_names)
            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerows([self.prepare_review_data(review) for review in reviews])

    def prepare_review_data(self, review):
        pictures = review.get("pictures", [])
        picture_urls = ";".join([picture["url"] for picture in pictures])
        report_result = review.get("reportResult", {})
        client_desc = report_result.get("clientDesc", "")
        desc = report_result.get("desc", "")
        create_time = self.convert_timestamp(review.get("createTime"))

        return {
            "评论ID": review.get("reviewId"),
            "用户ID": review.get("userId"),
            "商品ID": review.get("goodsId"),
            "订单ID": review.get("orderId"),
            "商家ID": review.get("mallId"),
            "评分": review.get("score"),
            "描述得分": review.get("descScore"),
            "物流得分": review.get("logisticsScore"),
            "服务得分": review.get("serviceScore"),
            "评论内容": review.get("comment"),
            "商品名称": review.get("goodsName"),
            "订单编号": review.get("orderSn"),
            "回复内容": review.get("reply") or "",
            "图片链接": picture_urls,
            "clientDesc": client_desc,
            "desc": desc,
            "评论时间": create_time
        }

    def convert_timestamp(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def reply_to_review(self, content, review_id):
        payload = {
            'content': content,
            "reviewId": review_id,
        }
        response = requests.post(self.reply_url, json=payload, headers=self.headers, cookies=self.cookies)
        return response.json()

    def auto_reply_reviews(self, update_callback):
        for review in self.reviews:
            if self.stop_replying:
                update_callback("用户停止了自动回复。")
                break
            service_score = review.get('serviceScore')
            review_id = review.get('reviewId')
            
            if service_score == 5:
                reply_content = self.get_reply_content_for_score(5)
            elif service_score == 4:
                reply_content = self.get_reply_content_for_score(4)
            else:
                reply_content = self.get_reply_content_for_score(3)

            response = self.reply_to_review(reply_content, review_id)
            if response.get('success') and response['errorCode'] == 1000000:
                update_callback(f"成功回复评论 ID: {review_id}")
            else:
                update_callback(f"回复评论 ID: {review_id} 失败")
            time.sleep(0.5)  # 控制回复频率
        update_callback("自动回复完成。")

    def get_reply_content_for_score(self, score):
        if score == 5:
            return self.custom_replies[5]
        elif score == 4:
            return self.custom_replies[4]
        else:
            return self.custom_replies[3]
        
    def set_custom_replies(self, custom_replies):
        self.custom_replies = custom_replies