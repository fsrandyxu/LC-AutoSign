import requests
from requests.exceptions import RequestException
import json
import hashlib
import time
import random
import os
from datetime import datetime

# ================= 全局配置区 =================
GLOBAL_METHOD = "add.signon.item"
GLOBAL_STYPE = 1

MILWAUKEETOOL_TOKEN_LIST = os.getenv('MILWAUKEETOOL_TOKEN_LIST', '')
MILWAUKEETOOL_CLIENT_ID = os.getenv('MILWAUKEETOOL_CLIENT_ID', '')
# SEND_KEY_LIST = os.getenv('SEND_KEY_LIST', '')
SERVERCHAN_SENDKEY = os.getenv('SERVERCHAN_SENDKEY', '')

# ========== 通知渠道：全部从环境变量读取 ==========
WECHAT_WEBHOOK_URL = os.getenv('WECHAT_WEBHOOK_URL', '')
DINGTALK_WEBHOOK_URL = os.getenv('DINGTALK_WEBHOOK_URL', '')

FAILED_LOG = []
RESULT_LOG = []

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


def format_sign_status(json_data, client_id=None):
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        if data.get('status') != 200:
            cid = f" | client_id: {client_id}" if client_id is not None else ""
            return f"❌ 错误：API 回应异常 (状态码: {data.get('status')}){cid}"

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
        output.append("【基本资讯】")
        if client_id is not None:
            output.append(f"  🆔 client_id：{client_id}")
        output.append(f"  🔐 签到状态：{status_text}")
        output.append(f"  📊 连续签到：{sign_count} 天")
        output.append(f"  📅 签到总数：{len(items)} 天")
        output.append("")

        if items:
            output.append("【签到记录】")
            sorted_items = sorted(items)
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

    except Exception as e:
        return f"❌ 格式化错误：{str(e)}"


# ========== 企业微信通知 ==========
def send_wechat_notification(failed_accounts, total_count, success_count):
    if not WECHAT_WEBHOOK_URL or WECHAT_WEBHOOK_URL.strip() == "":
        print("\n⚠️  未配置环境变量 WECHAT_WEBHOOK_URL，跳过企业微信推送")
        return

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fail_details = "\n".join([f"• {cid}: {reason}" for cid, reason in failed_accounts]) if failed_accounts else "无失败"

    content = (
        f"🤖 Milwaukee 签到任务执行报告\n"
        f"📅 时间: {now_str}\n"
        f"--------------------------\n"
        f"✅ 成功: {success_count} 个\n"
        f"❌ 失败: {len(failed_accounts)} 个\n"
        f"📦 总数: {total_count} 个\n"
        f"--------------------------\n"
        f"⚠️ 失败详情:\n{fail_details}"
    )

    payload = {
        "msgtype": "text",
        "text": {"content": content}
    }

    try:
        resp = requests.post(WECHAT_WEBHOOK_URL, json=payload, timeout=5)
        if resp.status_code == 200 and resp.json().get("errcode") == 0:
            print("\n✅ 企业微信通知发送成功")
        else:
            print(f"\n❌ 企业微信通知失败: {resp.text}")
    except Exception as e:
        print(f"\n❌ 企业微信发送异常: {str(e)}")


# ========== 钉钉机器人通知 ==========
def send_dingtalk_notification(failed_accounts, total_count, success_count, all_result):
    if not DINGTALK_WEBHOOK_URL or DINGTALK_WEBHOOK_URL.strip() == "":
        print("\n⚠️  未配置环境变量 DINGTALK_WEBHOOK_URL，跳过钉钉推送")
        return

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fail_details = "\n".join([f"• {cid}: {reason}" for cid, reason in failed_accounts]) if failed_accounts else "无失败"

    text = (
        f"### Milwaukee 签到结果\n"
        f"**时间**：{now_str}\n\n"
        f"✅ 成功：{success_count}/{total_count}\n"
        f"❌ 失败：{len(failed_accounts)}/{total_count}\n\n"
        f"**失败详情**：\n{fail_details}\n\n"
        f"**完整结果**：\n{all_result[:1500]}..."
    )

    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": "Milwaukee签到通知",
            "text": text
        }
    }

    try:
        resp = requests.post(DINGTALK_WEBHOOK_URL, json=msg, timeout=5)
        if resp.status_code == 200 and resp.json().get("errcode") == 0:
            print("✅ 钉钉通知发送成功")
        else:
            print(f"❌ 钉钉通知失败: {resp.text}")
    except Exception as e:
        print(f"❌ 钉钉发送异常: {str(e)}")


# ========== Server酱 ==========
def send_msg_by_server(send_key, title, content):
    push_url = f'https://sctapi.ftqq.com/{send_key}.send'
    data = {'text': title, 'desp': content}
    try:
        response = requests.post(push_url, data=data, timeout=10)
        return response.json()
    except RequestException:
        return None


def signAndList(token, client_id, account_index=1):
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
        msg = resp_json.get("msg", "") or resp_json.get("message", "") or str(resp_json)

        is_success = False
        if code == 200 or "成功" in msg or "已签到" in msg:
            is_success = True

        result_line = f"【账号 {account_index}】client_id: {client_id}\n结果：{'✅ 成功' if is_success else '❌ 失败'}\n信息：{msg}"
        RESULT_LOG.append(result_line)

        if is_success:
            print(f"      ✅ 结果: 成功 | {msg}")
            if SHOW_RAW_RESPONSE:
                print(f"      └─ 返回: {json.dumps(resp_json, ensure_ascii=False)}")

            print("\n📢 开始检查签到天数")
            time.sleep(random.uniform(1.0, 2.5))
            payload2 = {
                "token": token,
                "client_id": client_id,
                "appkey": APPKEY,
                "format": FORMAT,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "platform": PLATFORM,
                "method": "get.signon.list"
            }
            payload2["sign"] = generate_sign(payload2)
            resp2 = requests.post(URL, headers=HEADERS, json=payload2, timeout=20)
            signResult = format_sign_status(resp2.json(), client_id=client_id)
            print(signResult)

            return True
        else:
            print(f"      ❌ 结果: 失败 | {msg}")
            print(f"      └─ 完整返回: {json.dumps(resp_json, ensure_ascii=False, indent=2)}")
            FAILED_LOG.append((client_id, msg))
            return False

    except Exception as e:
        err = f"异常：{str(e)}"
        print(f"      ❌ {err}")
        RESULT_LOG.append(f"【账号 {account_index}】client_id: {client_id}\n{err}")
        FAILED_LOG.append((client_id, err))
        return False


def processAccount():
    tokenList = [t.strip() for t in MILWAUKEETOOL_TOKEN_LIST.split(',') if t.strip()]
    clientIdList = [cid.strip() for cid in MILWAUKEETOOL_CLIENT_ID.split(',') if cid.strip()]

    if not tokenList or not clientIdList:
        print("❌ 缺少 token 或 client_id")
        FAILED_LOG.append(("config", "缺少账号信息"))
        return 0, 0

    min_len = min(len(tokenList), len(clientIdList))
    tokenList = tokenList[:min_len]
    clientIdList = clientIdList[:min_len]

    print(f"🔧 共 {min_len} 个账号")

    success = 0
    for i, (token, cid) in enumerate(zip(tokenList, clientIdList), 1):
        print(f"\n{'─' * 50}")
        print(f"📌 账号 {i}/{min_len} | {cid}")
        print('─' * 50)
        if signAndList(token, cid, i):
            success += 1
    return success, min_len


def sendNotification():
    if not RESULT_LOG:
        RESULT_LOG.append("本次执行无任何账号返回信息")

    # 只改这里：只用同一个 SERVERCHAN_SENDKEY
    keys = [SERVERCHAN_SENDKEY.strip()]

    if not keys or not keys[0]:
        print("📤 未配置 SERVERCHAN_SENDKEY")
        return

    content = "\n\n".join(RESULT_LOG)
    print(f"📤 准备推送全部结果...")

    for key in keys:
        ret = send_msg_by_server(key, "Milwaukee 签到结果（成功/失败全推送）", content)
        if ret and ret.get("code") == 0:
            print(f"✅ Server酱推送成功 (key尾号:{key[-4:]})")
        else:
            print(f"❌ Server酱推送失败")


def main():
    print("=" * 60)
    print("🚀 Milwaukee 签到（全环境变量版）")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ========== 新增：每日仅签1次 核心逻辑 ==========
    import datetime
    import os
    today = datetime.date.today().strftime("%Y-%m-%d")
    # 用临时文件记录今日是否已签到（GitHub Actions 每次执行是新环境，改用日志判断）
    # 替代方案：读取签到结果里的「已签到」关键词，判断今日是否已签
    sign_result = ""
    try:
        # 先执行一次轻量查询，判断是否已签到（避免重复执行完整流程）
        tokenList = [t.strip() for t in MILWAUKEETOOL_TOKEN_LIST.split(',') if t.strip()]
        clientIdList = [cid.strip() for cid in MILWAUKEETOOL_CLIENT_ID.split(',') if cid.strip()]
        if tokenList and clientIdList:
            # 取第一个账号查询签到状态
            token = tokenList[0]
            cid = clientIdList[0]
            now = datetime.now()
            timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
            payload = {
                "token": token,
                "client_id": cid,
                "appkey": APPKEY,
                "format": FORMAT,
                "timestamp": timestamp_str,
                "platform": PLATFORM,
                "method": "get.signon.list"  # 仅查询，不签到
            }
            payload["sign"] = generate_sign(payload)
            resp = requests.post(URL, headers=HEADERS, json=payload, timeout=10)
            resp_json = resp.json()
            sign_data = resp_json.get('data', {})
            sign_status = sign_data.get('SigninStatus', 0)
            if sign_status == 1:
                print(f"✅ 检测到今日已签到（SigninStatus=1），本次执行跳过")
                print("=" * 60)
                return  # 直接退出，不执行后续签到
    except Exception as e:
        print(f"⚠️  查询签到状态失败，继续执行完整流程：{str(e)}")
    # ========== 防重复逻辑结束 ==========

    success_cnt, total_cnt = processAccount()
    all_result_str = "\n\n".join(RESULT_LOG)
    sendNotification()
    send_wechat_notification(FAILED_LOG, total_cnt, success_cnt)
    send_dingtalk_notification(FAILED_LOG, total_cnt, success_cnt, all_result_str)

    print("\n" + "=" * 60)
    print(f"🏁 完成 | 成功 {success_cnt}/{total_cnt} | 失败 {len(FAILED_LOG)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
