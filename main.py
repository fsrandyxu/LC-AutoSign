# -*- coding: UTF-8 -*-

import requests
import json
import time
import random
import os
from requests.exceptions import RequestException

TOKEN_LIST = os.getenv('TOKEN_LIST', '')
SERVERCHAN_SENDKEY = os.getenv('SERVERCHAN_SENDKEY', '')

# 接口配置
url = 'https://m.jlc.com/api/activity/sign/signIn?source=3'
gold_bean_url = "https://m.jlc.com/api/appPlatform/center/assets/selectPersonalAssetsInfo"
seventh_day_url = "https://m.jlc.com/api/activity/sign/receiveVoucher"
# 随机UA池
# 随机UA池（适配嘉立创，50条防重复）
UA_POOL = [
    # 嘉立创APP原生UA
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp",

    # iOS Safari UA
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 15_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",

    # Android Chrome UA
    "Mozilla/5.0 (Android 14; SM-S918B) AppleWebKit/537.36 Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 14; Pixel 8) AppleWebKit/537.36 Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 13; MI 13) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 12; SM-A528B) AppleWebKit/537.36 Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 11; Redmi Note 10) AppleWebKit/537.36 Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; vivo X100) AppleWebKit/537.36 Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; OPPO Find X6) AppleWebKit/537.36 Chrome/121.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; OnePlus 11) AppleWebKit/537.36 Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 14; HUAWEI Mate 60) AppleWebKit/537.36 Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 13; HUAWEI P60) AppleWebKit/537.36 Chrome/121.0.0.0 Mobile Safari/537.36",

    # MacOS Safari/Chrome UA
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0) AppleWebKit/605.1.15 Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 Chrome/119.0.0.0 Safari/537.36",

    # Windows Chrome/Edge UA
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
]


# ======== 工具函数 ========

def mask_account(account):
    """用于打印时隐藏部分账号信息"""
    if len(account) >= 4:
        return account[:2] + '****' + account[-2:]
    return '****'


def mask_json_customer_code(data):
    """递归地脱敏 JSON 中的 customerCode 字段"""
    if isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            if k == "customerCode" and isinstance(v, str):
                new_data[k] = v[:1] + "xxxxx" + v[-2:]
            else:
                new_data[k] = mask_json_customer_code(v)
        return new_data
    elif isinstance(data, list):
        return [mask_json_customer_code(i) for i in data]
    else:
        return data


# ======== 推送通知 ========

def send_msg_by_server(send_key, title, content):
    push_url = f'https://sctapi.ftqq.com/{send_key}.send'
    data = {
        'text': title,
        'desp': content
    }
    try:
        response = requests.post(push_url, data=data)
        return response.json()
    except RequestException:
        return None


# ======== 单个账号签到逻辑 ========

def sign_in(access_token):
# 每次随机取UA
random_ua = random.choice(UA_POOL)
headers = {
    'X-JLC-AccessToken': access_token,
    'User-Agent': random_ua,
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://m.jlc.com/',
    'Origin': 'https://m.jlc.com',
    'Connection': 'keep-alive',
    'platform': 'APP'
}


    try:
        # 1. 获取金豆信息（先获取，用于获取 customer_code）
        bean_response = requests.get(gold_bean_url, headers=headers)
        bean_response.raise_for_status()
        bean_result = bean_response.json()

        # 获取 customerCode
        customer_code = bean_result['data']['customerCode']
        integral_voucher = bean_result['data']['integralVoucher']

        # 2. 执行签到请求
        sign_response = requests.get(url, headers=headers)
        sign_response.raise_for_status()
        sign_result = sign_response.json()

        # 检查签到是否成功
        if not sign_result.get('success'):
            message = sign_result.get('message', '未知错误')
            if '已经签到' in message:
                print(f"ℹ️ [账号{mask_account(customer_code)}] 今日已签到")
                return None
            else:
                print(f"❌ [账号{mask_account(customer_code)}] 签到失败 - {message}")
                return None

        # 解析签到数据
        data = sign_result.get('data', {})
        gain_num = data.get('gainNum') if data else None
        status = data.get('status') if data else None

        # 处理签到结果
        if status and status > 0:
            if gain_num is not None and gain_num != 0:
                print(f"✅ [账号{mask_account(customer_code)}] 今日签到成功")
                return f"✅ 账号({mask_account(customer_code)})：获取{gain_num}个金豆，当前总数：{integral_voucher + gain_num}"
            else:
                # 第七天特殊处理
                seventh_response = requests.get(seventh_day_url, headers=headers)
                seventh_response.raise_for_status()
                seventh_result = seventh_response.json()

                if seventh_result.get("success"):
                    print(f"🎉 [账号{mask_account(customer_code)}] 第七天签到成功")
                    return f"🎉 账号({mask_account(customer_code)})：第七天签到成功，当前金豆总数：{integral_voucher + 8}"
                else:
                    print(f"ℹ️ [账号{mask_account(customer_code)}] 第七天签到失败，无金豆获取")
                    return None
        else:
            print(f"ℹ️ [账号{mask_account(customer_code)}] 今日已签到或签到失败")
            return None

    except RequestException as e:
        print(f"❌ [账号{mask_account(access_token)}] 网络请求失败: {str(e)}")
        return None
    except KeyError as e:
        print(f"❌ [账号{mask_account(access_token)}] 数据解析失败: 缺少键 {str(e)}")
        return None
    except Exception as e:
        print(f"❌ [账号{mask_account(access_token)}] 未知错误: {str(e)}")
        return None


# ======== 主函数 ========

def main():
    AccessTokenList = [token.strip() for token in TOKEN_LIST.split(',') if token.strip()]
    send_key = SERVERCHAN_SENDKEY.strip()

    if not AccessTokenList:
        print("❌ 请设置 TOKEN_LIST")
        return

    if not send_key:
        print("❌ 请设置 SERVERCHAN_SENDKEY")
        return

    print(f"🔧 共发现 {len(AccessTokenList)} 个账号需要签到")

    results = []
    for i, token in enumerate(AccessTokenList):
        print(f"\n📝 处理第 {i+1}/{len(AccessTokenList)} 个账号...")

        result = sign_in(token)
        if result is not None:
            results.append(result)

        if i < len(AccessTokenList) - 1:
            wait_time = random.randint(5, 15)
            print(f"⏳ 等待 {wait_time} 秒后处理下一个账号...")
            time.sleep(wait_time)

    # 统一推送一条
    print("\n📬 开始检查是否需要发送通知...")
    if results:
        content = "\n\n".join(results)
        response = send_msg_by_server(send_key, "嘉立创签到汇总", content)

        if response and response.get('code') == 0:
            print(f"✅ 通知发送成功！消息ID: {response.get('data', {}).get('pushid', '')}")
        else:
            error_msg = response.get('message') if response else '未知错误'
            print(f"❌ 通知发送失败！错误: {error_msg}")
    else:
        print("ℹ️ 所有账号均未获取到金豆，无通知发送")


# ======== 程序入口 ========

if __name__ == '__main__':
    print("🏁 嘉立创自动签到任务开始")
    main()
    print("🏁 任务执行完毕")
