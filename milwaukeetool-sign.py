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
SEND_KEY_LIST = os.getenv('SEND_KEY_LIST', '')
# 企业微信群机器人Webhook（替换为自己的真实key）
WECOM_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=00a9ed23-19e7-489b-b7b8-d7a4a6ae8cbe"

SECRET = "36affdc58f50e1035649abc808c22b48"
APPKEY = "76472358"
PLATFORM = "MP-WEIXIN"
FORMAT = "json"
URL = "https://service.milwaukeetool.cn/api/v1/signon"

HEADERS = {
    "Host": "service.milwaukeetool.cn",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF XWEB/18955",
    "xweb_xhr": "1",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://servicewechat.com/wxc13e77b0a12aac68/59/page-frame.html",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
# ===========================================

def generate_sign(params_dict):
    sorted_keys = sorted(params_dict.keys())
    s = SECRET
    for key in sorted_keys:
        val = params_dict[key]
        if isinstance(val, bool):
            val = 1 if val else 0
        s += str(key) + str(val)
    s += SECRET
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def format_sign_status(json_data):
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        if data.get('status') != 200:
            return f"❌ 错误：API响应异常 (状态码: {data.get('status')})"

        sign_data = data.get('data', {})
        sign_status = sign_data.get('SigninStatus', 0)
        sign_count = sign_data.get('signcount', 0)
        items = sign_data.get('items', [])
        send_num = sign_data.get('send_num', 0)
        used_num = sign_data.get('used_num', 0)
        available_num = sign_data.get('available_send_num', 0)

        output = []
        output.append("=" * 50)
        output.append(" 📋 签到系统状态报告 ".center(48, "="))
        output.append("=" * 50)
        output.append("")

        status_text = "✅ 已签到" if sign_status == 1 else "❌ 未签到"
        output.append(f"【基本信息】")
        output.append(f"  🔐 签到状态：{status_text}")
        output.append(f"  📊 连续签到：{sign_count} 天")
        output.append(f"  📅 签到总数：{len(items)} 天")
        output.append("")

        if items:
            output.append("【签到记录】")
            sorted_items = sorted(items)
            if len(sorted_items) > 1:
                try:
                    date_objs = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_items]
                    missing_dates = []
                    for i in range(len(date_objs) - 1):
                        current = date_objs[i]
                        next_date = date_objs[i + 1]
                        days_diff = (next_date - current).days
                        if days_diff > 1:
                            for j in range(1, days_diff):
                                missing = current.replace(day=current.day + j)
                                missing_dates.append(missing.strftime("%Y-%m-%d"))
                    for date in sorted_items:
                        output.append(f"  📆 {date} ✅")
                    if missing_dates:
                        output.append("")
                        output.append("【缺失记录】")
                        for date in missing_dates:
                            output.append(f"  📆 {date} ❌")
                except:
                    for date in sorted_items:
                        output.append(f"  📆 {date} ✅")
            else:
                for date in sorted_items:
                    output.append(f"  📆 {date} ✅")
        else:
            output.append("【签到记录】")
            output.append("  📭 暂无签到记录")

        output.append("")
        output.append("【使用统计】")
        output.append(f"  📤 今日发送：{send_num}")
        output.append(f"  📥 今日使用：{used_num}")
        output.append(f"  💾 可用额度：{available_num}")

        output.append("")
        output.append("=" * 50)
        output.append(f" 报告时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 50)

        return "\n".join(output)

    except json.JSONDecodeError as e:
        return f"❌ JSON解析错误：{str(e)}"
    except Exception as e:
        return f"❌ 格式化错误：{str(e)}"

# 新增：企业微信通知函数
def send_wecom_notify(content):
    if "你的真实机器人key" in WECOM_WEBHOOK:
        return
    try:
        payload = {
            "msgtype": "text",
            "text": {"content": content}
        }
        resp = requests.post(WECOM_WEBHOOK, json=payload, timeout=5)
        if resp.json().get("errcode") == 0:
            print("✅ 企业微信通知发送成功")
    except Exception as e:
        print(f"❌ 企业微信通知发送失败：{str(e)}")

def send_msg_by_server(send_key, title, content):
    push_url = f'https://sctapi.ftqq.com/{send_key}.send'
    data = {'text': title, 'desp': content}
    try:
        response = requests.post(push_url, data=data)
        return response.json()
    except:
        return None

# 新增：单账号处理函数（提取原单账号逻辑）
def process_single_account(token, client_id, acc_index):
    print(f"\n👉 处理第{acc_index}个账号")
    if not token or not client_id:
        err_msg = f"第{acc_index}个账号缺少token或client_id"
        print(f"❌ {err_msg}")
        send_wecom_notify(err_msg)
        return False

    token_show = f"{token[:6]}...{token[-4:]}" if len(token) > 10 else "***"
    print(f"      ├─ 方法: {GLOBAL_METHOD}")
    print(f"      ├─ ID: {client_id}")
    print(f"      └─ Token: {token_show}")

    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "token": token,
        "client_id": client_id,
        "appkey": APPKEY,
        "format": FORMAT,
        "timestamp": timestamp_str,
        "platform": PLATFORM,
        "method": GLOBAL_METHOD
    }

    if GLOBAL_METHOD == "add.signon.item":
        payload["year"] = str(now.year)
        payload["month"] = str(now.month)
        payload["day"] = str(now.day)
        payload["stype"] = GLOBAL_STYPE

    sign_val = generate_sign(payload)
    payload["sign"] = sign_val

    try:
        delay = random.uniform(1.0, 2.5)
        print(f"      ⏳ 等待 {delay:.1f}s...")
        time.sleep(delay)

        response = requests.post(URL, headers=HEADERS, json=payload, timeout=10)
        resp_json = response.json()
        code = resp_json.get("code")
        signStatus = resp_json.get("status")
        msg = resp_json.get("msg", "") or resp_json.get("message", "") or str(resp_json)
        is_success = False

        if code == 200:
            is_success = True
        elif "success" in str(resp_json).lower():
            is_success = True
        elif GLOBAL_METHOD == "add.signon.item" and ("已签到" in msg or "成功" in msg or "重复" in msg):
            is_success = True

        if is_success:
            print(f"      ✅ 结果: 成功 | {msg}")
            print(f"      └─ 返回: {json.dumps(resp_json, ensure_ascii=False)}")

            print("\n📢 开始检查签到天数")
            delay = random.uniform(1.0, 2.5)
            print(f"      ⏳ 等待 {delay:.1f}s...")
            time.sleep(delay)

            payload = {
                "token": token,
                "client_id": client_id,
                "appkey": APPKEY,
                "format": FORMAT,
                "timestamp": timestamp_str,
                "platform": PLATFORM,
                "method": "get.signon.list"
            }
            sign_val = generate_sign(payload)
            payload["sign"] = sign_val

            response = requests.post(URL, headers=HEADERS, json=payload, timeout=40)
            resp_json = response.json()
            signResult = format_sign_status(resp_json)
            print(f"{signResult}")

            if signStatus == 200 and SEND_KEY_LIST:
                print(f"📤 准备推送通知...")
                response = send_msg_by_server(SEND_KEY_LIST, f"第{acc_index}个账号签到汇总", signResult)
                if response and response.get('code') == 0:
                    print(f"✅ Server酱通知发送成功！")
                else:
                    print(f"❌ Server酱通知发送失败！")
            else:
                print(f"⏭️ 跳过通知")
            return True
        else:
            err_msg = f"第{acc_index}个账号签到失败(Code:{code})：{msg[:30]}"
            print(f"      ⚠️ {err_msg}")
            send_wecom_notify(err_msg)
            return False

    except Exception as e:
        err_msg = f"第{acc_index}个账号系统错误：{str(e)[:30]}"
        print(f"      ❌ {err_msg}")
        send_wecom_notify(err_msg)
        return False

def main():
    print("=" * 60)
    print(f"🚀 批量签到启动 | 模式: {GLOBAL_METHOD}")
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 读取双账号信息（逗号分隔）
    tokens = [t.strip() for t in os.getenv('MILWAUKETOOL_TOKEN_LIST', '').split(',') if t.strip()]
    client_ids = [c.strip() for c in os.getenv('MILWAUKETOOL_CLIENT_ID', '').split(',') if c.strip()]
    # 取最短长度，避免索引错误
    acc_count = min(len(tokens), len(client_ids))
    if acc_count == 0:
        print("❌ 未配置任何账号信息")
        return

    success_count = 0
    # 循环处理多账号
    for i in range(acc_count):
        if process_single_account(tokens[i], client_ids[i], i+1):
            success_count += 1
        # 账号间延时，避免请求频繁
        if i < acc_count - 1:
            time.sleep(random.uniform(1.0, 2.5))

    # 汇总结果
    print("\n" + "=" * 60)
    print(f"🏁 任务结束 | 成功: {success_count}/{acc_count}")
    print("=" * 60)
    # 汇总通知
    if success_count < acc_count:
        send_wecom_notify(f"批量签到完成，成功{success_count}个，失败{acc_count-success_count}个")

if __name__ == "__main__":
    main()
