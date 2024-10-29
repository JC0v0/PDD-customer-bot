import json
import requests
import csv
from datetime import datetime

url = "https://mms.pinduoduo.com/honolulu/after_sales_order/paging"

headers = {
    "Cookie": "terminalFinger=PwxyByjvSmQLC6VOwen0mqYDE1MaoTYb; _f77=e53d06e3-6a8e-4102-ae5f-9aea00a81053; ru1k=e53d06e3-6a8e-4102-ae5f-9aea00a81053; _bee=IRGYnKcC6PUH7TAJwX0CE4aD0d4BlYDX; _a42=542a1cff-f0d6-4c54-8eac-3982ce07161c; rckk=IRGYnKcC6PUH7TAJwX0CE4aD0d4BlYDX; ru2k=542a1cff-f0d6-4c54-8eac-3982ce07161c; api_uid=rBU0B2ZqmiZbdXLVKIthAg==; _nano_fp=Xpmal0PjX5dblpX8nC_dPU6dPhXuJAP545~YX_I_; PASS_ID=1-Ys2y6EOzbg6M5V/7J0P5Q1KmdUq3TcaxmJOcXsgsJbqFoWpsYnqIQp2f1nGOTImTT9nMSoCyzP5ZNPUYrdJxhw_591119888_149439461; webp=true; x-visit-time=1726111009776; mms_b84d1838=150,3523,3614,3612,3587,3588,3254,3531,3470,3474,3475,3477,3479,3482,1202,1203,1204,1205,3417,3397; JSESSIONID=2EB329D3CD1106B68A83790DAFE42820"
}

payload = {
    "keyList": [],
    "startTime": "1724860800000",
    "endTime": "1726156799999",
    "statistics": True,
    "shippingTmsStatusList": [],
    "tmsReturnStatusList": [],
    "tempNewFrontVersion1008": True,
    "mallIdList": [],
    "timeType": "refundUpdateTime",
    "processStatus": 0,
    "shippingId": "",
    "page": 1,
    "pageSize": 1000
}

response = requests.post(url, json=payload, headers=headers)

# 保存返回的订单信息到 CSV 文件
if response.status_code == 200:
    data = response.json()
    orders_list = data['result']['orders']['list']
    
    with open('订单信息.csv', 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = [
            "商场ID", "订单ID", "用户ID", "售后ID", "订单编号", "售后类型", 
            "售后状态", "售后原因", "是否快速退款", "是否争议退款", 
            "打印状态", "发货状态", "发货时间", "物流追踪号码", 
            "退款金额", "退款创建时间", "退款更新时间", "订单金额", 
            "商品名称", "商品规格", "商品数量", "商品缩略图", "商店名称"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()  # 写入表头
        
        for order in orders_list:
            order_data = {
                "商场ID": order["mallId"],
                "订单ID": order["id"],
                "用户ID": order["honoluluUid"],
                "售后ID": order["afterSalesId"],
                "订单编号": order["orderSn"],
                "售后类型": order["afterSalesType"],
                "售后状态": order["afterSalesStatus"],
                "售后原因": order["afterSalesReason"],
                "是否快速退款": order["isSpeedRefund"],
                "是否争议退款": order["isDisputeRefund"],
                "打印状态": order["printStatus"],
                "发货状态": order["shippingStatus"],
                "发货时间": datetime.fromtimestamp(order["shippingTime"] / 1000).strftime('%Y-%m-%d %H:%M:%S') if order["shippingTime"] else "未发货",  # 处理 None 值
                "物流追踪号码": order["trackingNumber"],
                "退款金额": f"{order['refundAmount'] / 100:.2f}",  # 格式化为 27.28
                "退款创建时间": datetime.fromtimestamp(order["refundCreateTime"] / 1000).strftime('%Y-%m-%d %H:%M:%S'),  # 转换为可读格式
                "退款更新时间": datetime.fromtimestamp(order["refundUpdateTime"] / 1000).strftime('%Y-%m-%d %H:%M:%S'),  # 转换为可读格式
                "订单金额": f"{order['orderAmount'] / 100:.2f}",  # 格式化为 27.28
                "商品名称": order["goodsName"],
                "商品规格": order["spec"],
                "商品数量": order["goodsNumber"],
                "商品缩略图": order["thumbUrl"],
                "商店名称": order["mallName"],
            }
            writer.writerow(order_data)  # 写入每一行数据
            
    print("订单信息已成功保存到 订单信息.csv")
else:
    print(f"请求失败，状态码: {response.status_code}")

