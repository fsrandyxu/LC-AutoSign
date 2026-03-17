import requests
import json
import hashlib
import time
import random
import os
from datetime import datetime

# ================= 全局配置 =================
GLOBAL_METHOD = "add.signon.item"
GLOBAL_STYPE = 1

# 多账号读取（逗号分隔）
SEND_KEY_LIST = os.getenv('SEND_KEY_LIST', '').split(',')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
TOKEN_LIST = os.getenv('MILWAUKEETOOL_TOKEN_LIST', '').split(',')
CLIENT_ID_LIST = os.getenv('MILWAUKEETOOL_CLIENT_ID', '').split(',')

# 接口固定配置
SECRET = "36affdc58f50e1035649abc808c22b48"
APPKEY = "76472358"
PLATFORM = "MP-WEIXIN"
FORMAT = "json"
URL = "https://service.milwaukeetool.cn/api/v1/signon"

# 请求头
HEADERS = {
    "Host": "service.milwaukeetool.cn",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat(0x63090a13) XWEB/11899",
    "xweb_xhr": "1",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://servicewechat.com/wxc13e77b0a12aac68/59/page-frame.html",
    "Accept-Encoding": "gzip, deflate, br"
}

# ================= 网络重试 =================
def request_with_retry(url, headers=None, json=None, timeout=15, retry=3):
    headers = headers or {}
    json = json or {}
    for i in range(retry):
        try:
            resp = requests.post(url, headers=headers, json=json, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            print(f"⚠️  第{i+1}次请求失败：{str(e)[:40]}")
            time.sleep(1)
    raise Exception("请求3次均失败")

# ================= 签名 =================
def generate_sign(params):
    sorted_keys = sorted(params.keys())
    s = SECRET
    for k in sorted_keys:
        v = params[k]
        s += str(k) + str(v)
    s += SECRET
    return hashlib.md5(s.encode("utf-8")).hexdigest()

# ================= 单账号处理 =================
def handle_account(token, client_id, index):
    if not token or not client_id:
        print(f"⚠️  账号 {index}：凭证缺失")
        return False

    now = datetime.now()
    ts = now.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "token": token,
        "client_id": client_id,
        "appkey": APPKEY,
        "format": FORMAT,
        "timestamp": ts,
        "platform": PLATFORM,
        "method": GLOBAL_METHOD
    }

    if GLOBAL_METHOD == "add.signon.item":
        payload["year"] = str(now.year)
        payload["month"] = str(now.month)
        payload["day"] = str(now.day)
        payload["stype"] = GLOBAL_STYPE

    try:
        time.sleep(random.uniform(1, 2.5))
        payload["sign"] = generate_sign(payload)
        resp = request_with_retry(URL, headers=HEADERS, json=payload)
        data = resp.json()
        code = data.get("code")

        if code == 200 or "success" in str(data).lower() or "已签到" in str(data):
            print(f"✅ 账号 {index} 签到成功")
            return True
        else:
            print(f"❌ 账号 {index} 签到失败：{data.get('msg', '无返回信息')}")
            return False
    except Exception as e:
        print(f"❌ 账号 {index} 异常：{str(e)[:40]}")
        return False

# ================= 主程序（多账号循环） =================
def main():
    print("=" * 40)
    print("密尔沃基多账号签到任务启动")
    print(f"检测到账号数：{len(TOKEN_LIST)}")
    print("=" * 40)

    success = 0
    failed = 0

    for i in range(len(TOKEN_LIST)):
        token = TOKEN_LIST[i].strip()
        cid = CLIENT_ID_LIST[i].strip() if i < len(CLIENT_ID_LIST) else ""

        if handle_account(token, cid, i + 1):
            success += 1
        else:
            failed += 1

    print("=" * 40)
    print(f"任务结束：成功 {success} | 失败 {failed}")
    print("=" * 40)

if __name__ == "__main__":
    main()
