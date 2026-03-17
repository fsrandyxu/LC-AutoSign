import requests
import json
import hashlib
import time
import random
import os
from datetime import datetime
# ================= 全局配置区 =================
GLOBAL_METHOD = "add.signon.item"
GLOBAL_STYPE = 1
SEND_KEY_LIST = os.getenv('SEND_KEY_LIST', '')
# 企业微信Webhook（替换为你的真实key）
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=00a9ed23-19e7-489b-b7b8-d7a4a6ae8cbe"
SHOW_RAW_RESPONSE = True
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541739) XWEB/18955",
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

def send_wechat_notification(failed_accounts, total_count, success_count):
    if not WEBHOOK_URL or "你的群机器人key" in WEBHOOK_URL:
        print("\n⚠️  未配置有效Webhook，跳过企微通知。")
        return
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fail_details = "\n".join([f"• 账号{idx}: {reason}" for idx, reason in failed_accounts])
    content = (
        f"🤖 **签到任务执行报告**\n"
        f"📅 时间: {now_str}\n"
        f"--------------------------\n"
        f"✅ 成功: {success_count} 个\n"
        f"❌ 失败: {len(failed_accounts)} 个\n"
        f"📂 总数: {total_count} 个\n"
        f"--------------------------\n"
        f"⚠️ **失败详情:**\n{fail_details}"
    )
    payload = {"msgtype": "text", "text": {"content": content}}
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        if resp.status_code == 200 and resp.json().get("errcode") == 0:
            print("\n📢 企微通知发送成功。")
        else:
            print(f"\n⚠️  企微通知失败: {resp.text}")
    except Exception as e:
        print(f"\n⚠️  企微通知异常: {str(e)}")

def send_msg_by_server(send_key, title, content):
    push_url = f'https://sctapi.ftqq.com/{send_key}.send'
    data = {'text': title, 'desp': content}
    try:
        response = requests.post(push_url, data=data)
        return response.json()
    except Exception:
        return None

def process_account(index, total, failed_list):
    # 读取并分割账号配置，加校验避免索引错误
    token_list = [t.strip() for t in os.getenv('MILWAUKETOOL_TOKEN_LIST', '').split(',') if t.strip()]
    client_id_list = [c.strip() for c in os.getenv('MILWAUKETOOL_CLIENT_ID', '').split(',') if c.strip()]
    # 校验账号配置是否存在
    if index-1 >= len(token_list) or index-1 >= len(client_id_list):
        msg = "账号配置缺失（未找到第{}个账号的token/id）".format(index)
        print(f"      ❌ 结果: {msg}")
        failed_list.append((index, msg))
        return False
    token = token_list[index-1]
    client_id = client_id_list[index-1]
    token_show = f"{token[:6]}...{token[-4:]}" if len(token) > 10 else "***"
    print(f"      ├─ 方法: {GLOBAL_METHOD}")
    print(f"      ├─ ID: {client_id}")
    print(f"      └─ Token: {token_show}")
    if not token or not client_id:
        msg = "缺少token或client_id"
        print(f"      ❌ 结果: {msg}")
        failed_list.append((index, msg))
        return False
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
        if code == 200 or "success" in str(resp_json).lower() or (GLOBAL_METHOD == "add.signon.item" and ("已签到" in msg or "成功" in msg or "重复" in msg)):
            is_success = True
        if is_success:
            print(f"      ✅ 结果: 成功 | {msg}")
            if SHOW_RAW_RESPONSE:
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
                print(f"📤 准备发送Server酱通知...")
                response = send_msg_by_server(SEND_KEY_LIST, "milwaukeetool签到汇总", signResult)
                if response and response.get('code') == 0:
                    print(f"✅ Server酱通知成功！消息ID: {response.get('data', {}).get('pushid', '')}")
                else:
                    error_msg = response.get('message') if response else '未知错误'
                    print(f"❌ Server酱通知失败！错误: {error_msg}")
            else:
                print(f"⏭️ SendKey未配置/无签到，跳过通知")
            return True
        else:
            print(f"      ⚠️ 结果: 失败 (Code:{code}) | {msg}")
            print(f"      └─ 完整返回:\n{json.dumps(resp_json, ensure_ascii=False, indent=4)}")
            short_msg = msg if len(msg) < 50 else msg[:47] + "..."
            failed_list.append((index, f"{short_msg} (Code:{code})"))
            return False
    except Exception as e:
        err_msg = str(e)
        print(f"      ❌ 结果: 网络/系统错误 - {err_msg}")
        failed_list.append((index, f"网络错误: {err_msg}"))
        return False

def main():
    print("=" * 60)
    print(f"🚀 批量签到启动 | 模式: {GLOBAL_METHOD}")
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    success_count = 0
    failed_list = []
    # 配置要执行的账号数量（改为1就是单账号，2就是双账号）
    TOTAL_ACCOUNT = 2
    # 循环执行签到
    for i in range(1, TOTAL_ACCOUNT+1):
        print(f"\n👉 开始处理第{i}个账号/{TOTAL_ACCOUNT}个")
        if process_account(i, TOTAL_ACCOUNT, failed_list):
            success_count += 1
        if i < TOTAL_ACCOUNT:
            inter_delay = random.uniform(1.0, 2.5)
            print(f"\n⏳ 账号间等待 {inter_delay:.1f}s...")
            time.sleep(inter_delay)
    # 汇总结果
    print("\n" + "=" * 60)
    print(f"🏁 任务结束")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失败: {len(failed_list)}")
    print("=" * 60)
    # 发送企业微信通知
    if len(failed_list) > 0:
        send_wechat_notification(failed_list, TOTAL_ACCOUNT, success_count)
        print("\n存在失败账号，已尝试发送企微通知。")
    else:
        print("\n🎉 全部成功，无需发送通知。")

if __name__ == "__main__":
    main()
