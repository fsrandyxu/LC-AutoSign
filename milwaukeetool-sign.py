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
SEND_KEY_LIST = [k.strip() for k in os.getenv('SEND_KEY_LIST', '').split(',') if k.strip()]
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').strip()
TOKEN_LIST = [t.strip() for t in os.getenv('MILWAUKETOOL_TOKEN_LIST', '').split(',') if t.strip()]
CLIENT_ID_LIST = [c.strip() for c in os.getenv('MILWAUKETOOL_CLIENT_ID_LIST', '').split(',') if c.strip()]

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
    "Referer": "https://servicewechat.com/wxc13e77b0aac68/59/page-frame.html",
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
            if i < retry - 1:
                time.sleep(2)
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

# ================= Server酱通知 =================
def send_server_notice(title, content, send_key):
    if not send_key:
        print("ℹ️  Server酱Key为空，跳过通知")
        return False
    try:
        url = f"https://sctapi.ftqq.com/{send_key}.send"
        data = {"title": title, "desp": content}
        resp = requests.post(url, data=data, timeout=10)
        resp_json = resp.json()
        if resp_json.get("code") == 0:
            print(f"✅ Server酱通知发送成功：{resp_json.get('data', {}).get('pushid')}")
            return True
        else:
            print(f"❌ Server酱通知失败：{resp_json.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Server酱通知异常：{str(e)[:40]}")
        return False

# ================= 企业微信通知 =================
def send_wechat_notice(content):
    if not WEBHOOK_URL:
        print("ℹ️  企业微信Webhook为空，跳过通知")
        return False
    try:
        data = {"msgtype": "text", "text": {"content": content}}
        resp = requests.post(WEBHOOK_URL, json=data, timeout=10)
        resp_json = resp.json()
        if resp_json.get("errcode") == 0:
            print("✅ 企业微信通知发送成功")
            return True
        else:
            print(f"❌ 企业微信通知失败：{resp_json.get('errmsg')}")
            return False
    except Exception as e:
        print(f"❌ 企业微信通知异常：{str(e)[:40]}")
        return False

# ================= 单账号处理 =================
def handle_account(token, client_id, index):
    if not token or not client_id:
        msg = f"MILWAUKETOOL 账号{index}：凭证缺失"
        print(f"❌ {msg}")
        return False, msg

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
        time.sleep(random.uniform(3, 5))
        payload["sign"] = generate_sign(payload)
        resp = request_with_retry(URL, headers=HEADERS, json=payload)
        data = resp.json()
        code = data.get("code")

        if code == 200 or "success" in str(data).lower() or "已签到" in str(data):
            msg = f"MILWAUKETOOL 账号{index} 签到成功"
            print(f"✅ {msg}")
            return True, msg
        else:
            msg = f"MILWAUKETOOL 账号{index} 签到失败：{data.get('msg', '无返回信息')}"
            print(f"❌ {msg}")
            return False, msg
    except Exception as e:
        msg = f"MILWAUKETOOL 账号{index} 异常：{str(e)[:40]}"
        print(f"❌ {msg}")
        return False, msg

# ================= 主程序（多账号循环） =================
def main():
    print("========================================")
    print("MILWAUKETOOL 多账号签到任务启动")
    print(f"检测到账号数：{len(TOKEN_LIST)}")
    print("========================================")

    success = 0
    failed = 0
    log_list = []

    for i in range(len(TOKEN_LIST)):
        token = TOKEN_LIST[i]
        cid = CLIENT_ID_LIST[i] if i < len(CLIENT_ID_LIST) else ""
        res, msg = handle_account(token, cid, i + 1)
        log_list.append(msg)
        if res:
            success += 1
        else:
            failed += 1

    # 汇总标题与内容（全部大写 MILWAUKETOOL）
    title = f"MILWAUKETOOL 签到结果 成功{success} 失败{failed}"
    summary = f"""
MILWAUKETOOL 签到任务汇总
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
账号总数：{len(TOKEN_LIST)}
成功：{success} | 失败：{failed}

详细结果：
{chr(10).join(log_list)}
    """

    print("========================================")
    print(f"任务结束：成功 {success} | 失败 {failed}")
    print("========================================")

    # 发送通知
    print("\n📢 开始发送通知...")
    send_key = SEND_KEY_LIST[i] if i < len(SEND_KEY_LIST) else (SEND_KEY_LIST[0] if SEND_KEY_LIST else "")
    send_server_notice(title, summary, send_key)
    send_wechat_notice(summary.strip())

if __name__ == "__main__":
    main()
