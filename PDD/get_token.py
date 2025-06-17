import requests
import json
from utils.logger import get_logger
logger = get_logger(__name__)

def get_token(account_name):
    """
    根据提供的店铺名获取对应的token
    Returns:
        str: 成功返回token字符串
        None: 获取失败返回None
    """
        
    url = "https://mms.pinduoduo.com/chats/getToken"
    payload = {
        'version': '3'
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
        'anti-content': "0apAfqnpGOtaj99D70TYuvfGIZyE6nYmcn1OuC7OO1-vZayu54U_uKmNy3hSXyCJWTGM6vysoase3JNsgm5R9sq0VabIq8-vBf_dGi3DZ-M01vwzSWTijX8PSBvVTveXc_VLwZyLOOfSTBswz_ozPWLJUM_bnZkf4ZNPMgZ35MR9fkLL0jHDMEcOoor19ZaIgVEbzzX2vwsHZ0tztafCSGbNkkKW7buubajzmWXtFQ0M6ZA9dzz987vXgF9aiT39-m2OpjTBl0Z4-C9mpS_uDU4zF6U8vnrQZ9dZFV-HTptCc3g6wb45rC8Ln--Bje9xyF4JbEPsrRc9sWBaU5PJ8wpjZGW4BPIjlfxIX7zIpDwHc6kl2cAxvyVjrvNunJvej6obucnKr8l1xfOlFhyGyA-h8YQG4LWO3knxHolBclEWuRccC4X5M-ffEfHZ9c",
        'priority': "u=1, i"
    }
    with open('config/cookies.json', 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    try:
        
        response = requests.post(url, data=payload, headers=headers, cookies=cookies)
        
        # 检查响应状态
        if response.status_code == 200:
            try:
                result = response.json()
                if 'token' in result:
                    logger.info(f"成功获取账号 {account_name} 的token")
                    return result['token']
                elif 'result' in result and 'token' in result['result']:
                    logger.info(f"成功获取账号 {account_name} 的token")
                    return result['result']['token']
                else:
                    logger.error(f"账号 {account_name} 无法从响应中获取token: {response.text}")
            except Exception as e:
                logger.error(f"账号 {account_name} 解析响应JSON失败: {str(e)}")
        else:
            logger.error(f"账号 {account_name} 请求失败，状态码: {response.status_code}")
            
    except KeyError as e:
        logger.error(f"账号 {account_name} 账号数据结构不正确: {str(e)}")
    except requests.RequestException as e:
        logger.error(f"账号 {account_name} 请求异常: {str(e)}")
    except Exception as e:
        logger.error(f"账号 {account_name} 获取token时发生未知错误: {str(e)}")
        
    return None