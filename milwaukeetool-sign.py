import requests
import json
import hashlib
import time
import random
import os
from datetime import datetime
from pathlib import Path

# ================= 全局配置区（全部从环境变量读取，无硬编码）=================
# 【核心开关】签到/查询开关
GLOBAL_METHOD = "add.signon.item"  # 执行签到
# GLOBAL_METHOD = "get.signon.list"  # 仅查询签到天数
GLOBAL_STYPE = 1

# 从环境变量读取密钥（与GitHub Secrets完全匹配）
SEND_KEY_LIST = os.getenv('SEND_KEY_LIST', '')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
MILWAUKEETOOL_TOKEN_LIST = os.getenv('MILWAUKEETOOL_TOKEN_LIST', '')
MILWAUKEETOOL_CLIENT_ID = os.getenv('MILWAUKEETOOL_CLIENT_ID', '')

# 【调试开关】True打印完整返回，False仅失败打印
SHOW_RAW_RESPONSE = True

# 接口固定配置（勿改）
SECRET = "36affdc58f50e1035649abc808c22b48"
APPKEY = "76472358"
PLATFORM = "MP-WEIXIN"
FORMAT = "json"
URL = "https://service.milwaukeetool.cn/api/v1/signon"

# 请求头（勿改）
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

# 网络请求重试函数（解决GitHub海外服务器访问超时）
def request_with_retry(url, headers=None, json=None, timeout=10, retry=3):
    """带重试的POST请求，默认重试3次"""
    headers = headers or {}
    json = json or {}
    for i in range(retry):
        try:
            response = requests.post(url, headers=headers, json=json, timeout=timeout)
            response.raise_for_status()  # 触发HTTP错误
            return response
        except requests.RequestException as e:
            print(f"      ⚠️  请求失败（第{i+1}次）：{str(e)[:50]}，1秒后重试...")
            time.sleep(1)
    raise Exception(f"请求{retry}次均失败，终止操作")

def generate_sign(params_dict):
    """生成接口签名（核心方法）"""
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
    """格式化签到状态为易读文本"""
    try:
        data = json.loads(json_data) if isinstance(json_data, str) else json_data
        if data.get('status') != 200:
            return f"❌ 错误：API 响应异常 (状态码: {data.get('status')})"
        
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
        output.append(f"【使用统计】")
        output.append(f"  📤 今日发送：{send_num}")
        output.append(f"  📥 今日使用：{used_num}")
        output.append(f"  💾 可用额度：{available_num}")
        output.append("")
        output.append("=" * 50)
        output.append(f" 报告时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 50)
        
        return "\n".join(output)
    except json.JSONDecodeError as e:
        return f"❌ JSON 解析错误：{str(e)}"
    except Exception as e:
        return f"❌ 格式化错误：{str(e)}"

def get_markdown_format(json_data):
    """生成Markdown格式报告"""
    try:
        data = json.loads(json_data) if isinstance(json_data, str) else json_data
        if data.get('status') != 200:
            return f"❌ 错误：API 响应异常 (状态码: {data.get('status')})"
        
        sign_data = data.get('data', {})
        sign_status = sign_data.get('SigninStatus', 0)
        sign_count = sign_data.get('signcount', 0)
        items = sign_data.get('items', [])
        status_text = "✅ 已签到" if sign_status == 1 else "❌ 未签到"
        
        markdown = []
        markdown.append("## 📊 签到状态报告")
        markdown.append("")
        markdown.append("| 项目 | 状态 |")
        markdown.append("|------|------|")
        markdown.append(f"| 🔐 签到状态 | {status_text} |")
        markdown.append(f"| 📊 连续签到天数 | {sign_count} 天 |")
        if items:
            items_str = ", ".join(items)
            markdown.append(f"| 📆 签到记录 | {items_str} |")
            markdown.append("")
            markdown.append("### 📝 签到明细")
            for date in sorted(items):
                markdown.append(f"- {date} ✅")
        else:
            markdown.append(f"| 📆 签到记录 | 暂无记录 |")
        return "\n".join(markdown)
    except Exception as e:
        return f"❌ 格式化错误：{str(e)}"

def send_wechat_notification(failed_accounts, total_count, success_count):
    """发送企业微信失败通知"""
    if not WEBHOOK_URL or "key=" not in WEBHOOK_URL or len(WEBHOOK_URL.split("key=")[-1]) < 10:
        print("\n⚠️  未配置有效的企业微信Webhook URL，跳过通知发送。")
        return
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fail_details = "\n".join([f"• {name}: {reason}" for name, reason in failed_accounts]) if failed_accounts else "无详细原因"
    content = (
        f"🤖 **milwaukeetool签到任务执行报告**\n"
        f"📅 执行时间: {now_str}\n"
        f"--------------------------\n"
        f"✅ 成功账号: {success_count} 个\n"
        f"❌ 失败账号: {len(failed_accounts)} 个\n"
        f"📂 总账号数: {total_count} 个\n"
        f"--------------------------\n"
        f"⚠️ **失败详情:**\n{fail_details}"
    )
    payload = {"msgtype": "text", "text": {"content": content}}
    try:
        resp = request_with_retry(WEBHOOK_URL, json=payload, timeout=8)
        if resp.json().get("errcode") == 0:
            print("\n📢 企业微信失败通知发送成功。")
        else:
            print(f"\n⚠️  企业微信通知发送失败: {resp.json().get('errmsg', '未知错误')}")
    except Exception as e:
        print(f"\n⚠️  企业微信通知发送异常: {str(e)}")

# ======== Server酱通知模块 ========
def send_msg_by_server(send_key, title, content):
    """Server酱通用推送"""
    if not send_key or len(send_key) < 10:
        print("⚠️  Server酱SendKey无效，跳过推送。")
        return None
    push_url = f'https://sctapi.ftqq.com/{send_key}.send'
    data = {'text': title, 'desp': content}
    try:
        resp = request_with_retry(push_url, data=data, timeout=8)
        return resp.json()
    except Exception:
        return None

def send_fail_msg(send_key, fail_reason):
    """Server酱失败专用推送"""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    content = f"""
### ❌ 【密尔沃基】签到失败
**失败时间**：{now_str}
**失败账号**：默认账号
**失败原因**：{fail_reason}
"""
    res = send_msg_by_server(send_key, '【紧急】【密尔沃基】签到失败！', content)
    if res and res.get('code') == 0:
        print(f"✅ Server酱失败通知发送成功！消息ID: {res.get('data', {}).get('pushid', '')}")
    else:
        print(f"❌ Server酱失败通知发送失败！错误: {res.get('message', '未知错误') if res else '网络异常'}")

def process_account(account_info, index, total, failed_list):
    """处理单个账号签到"""
    # 脱敏显示凭证
    token_show = f"{MILWAUKEETOOL_TOKEN_LIST[:6]}...{MILWAUKEETOOL_TOKEN_LIST[-4:]}" if len(MILWAUKEETOOL_TOKEN_LIST) > 10 else "***"
    print(f"\n📌 处理账号 {index}/{total}")
    print(f"      ├─ 接口: {GLOBAL_METHOD}")
    print(f"      ├─ ClientID: {MILWAUKEETOOL_CLIENT_ID}")
    print(f"      └─ Token: {token_show}")
    
    # 凭证空值校验
    if not MILWAUKEETOOL_TOKEN_LIST or not MILWAUKEETOOL_CLIENT_ID:
        msg = "核心凭证缺失：未配置MILWAUKEETOOL_TOKEN_LIST或MILWAUKEETOOL_CLIENT_ID"
        print(f"      ❌ 结果: {msg}")
        failed_list.append(("默认账号", msg))
        if SEND_KEY_LIST:
            send_fail_msg(SEND_KEY_LIST, msg)
        return False
    
    # 构造基础参数
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "token": MILWAUKEETOOL_TOKEN_LIST,
        "client_id": MILWAUKEETOOL_CLIENT_ID,
        "appkey": APPKEY,
        "format": FORMAT,
        "timestamp": timestamp_str,
        "platform": PLATFORM,
        "method": GLOBAL_METHOD
    }
    # 签到接口专属参数
    if GLOBAL_METHOD == "add.signon.item":
        payload["year"] = str(now.year)
        payload["month"] = str(now.month)
        payload["day"] = str(now.day)
        payload["stype"] = GLOBAL_STYPE
    
    # 生成签名并请求
    try:
        time.sleep(random.uniform(1.0, 2.5))  # 防频率限制
        payload["sign"] = generate_sign(payload)
        response = request_with_retry(URL, headers=HEADERS, json=payload, timeout=10)
        resp_json = response.json()
        code = resp_json.get("code", -1)
        msg = resp_json.get("msg", "") or resp_json.get("message", "") or "无返回信息"
        is_success = False

        # 签到成功判定逻辑
        if code == 200 or "success" in str(resp_json).lower():
            is_success = True
        elif GLOBAL_METHOD == "add.signon.item" and ("已签到" in msg or "成功" in msg or "重复" in msg):
            is_success = True

        if is_success:
            print(f"      ✅ 结果: 执行成功 | {msg}")
            if SHOW_RAW_RESPONSE:
                print(f"      └─ 接口返回: {json.dumps(resp_json, ensure_ascii=False)}")
            
            # 仅签到成功后，查询签到天数
            if GLOBAL_METHOD == "add.signon.item":
                print("\n📢 开始查询签到天数...")
                time.sleep(random.uniform(1.0, 2.5))
                # 构造查询参数
                query_payload = {
                    "token": MILWAUKEETOOL_TOKEN_LIST,
                    "client_id": MILWAUKEETOOL_CLIENT_ID,
                    "appkey": APPKEY,
                    "format": FORMAT,
                    "timestamp": timestamp_str,
                    "platform": PLATFORM,
                    "method": "get.signon.list"
                }
                query_payload["sign"] = generate_sign(query_payload)
                query_resp = request_with_retry(URL, headers=HEADERS, json=query_payload, timeout=10)
                query_json = query_resp.json()
                signResult = format_sign_status(query_json)
                print(f"{signResult}")

                # 发送Server酱成功通知
                query_status = query_json.get("status", -1)
                if query_status == 200 and SEND_KEY_LIST:
                    print(f"\n📤 准备发送Server酱成功通知...")
                    res = send_msg_by_server(SEND_KEY_LIST, "✅ 【密尔沃基】签到成功", signResult)
                    if res and res.get('code') == 0:
                        print(f"✅ Server酱成功通知发送成功！消息ID: {res.get('data', {}).get('pushid', '')}")
                    else:
                        print(f"❌ Server酱成功通知发送失败！错误: {res.get('message', '未知错误') if res else '网络异常'}")
            return True
        else:
            # 执行失败处理
            fail_reason = f"{msg} (接口返回码: {code})"
            print(f"      ⚠️  结果: 执行失败 | {fail_reason}")
            if SHOW_RAW_RESPONSE:
                print(f"      └─ 接口返回:\n{json.dumps(resp_json, ensure_ascii=False, indent=4)}")
            failed_list.append(("默认账号", fail_reason[:100]))
            if SEND_KEY_LIST:
                send_fail_msg(SEND_KEY_LIST, fail_reason)
            return False
    except Exception as e:
        # 异常处理
        fail_reason = f"网络/接口异常：{str(e)[:80]}"
        print(f"      ❌ 结果: {fail_reason}")
        failed_list.append(("默认账号", fail_reason))
        if SEND_KEY_LIST:
            send_fail_msg(SEND_KEY_LIST, fail_reason)
        return False

def main():
    """主函数"""
    print("=" * 60)
    print(f"🚀 milwaukeetool自动签到启动")
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 执行模式: {GLOBAL_METHOD.replace('.', '_')}")
    print("=" * 60)
    
    success_count = 0
    failed_list = []
    # 执行单个账号签到
    if process_account(None, 1, 1, failed_list):
        success_count += 1

    # 任务汇总
    print("\n" + "=" * 60)
    print(f"🏁 签到任务执行完毕")
    print(f"   ✅ 成功: {success_count} 个账号")
    print(f"   ❌ 失败: {len(failed_list)} 个账号")
    print("=" * 60)
    
    # 失败则发送企业微信通知
    if len(failed_list) > 0:
        send_wechat_notification(failed_list, 1, success_count)
    else:
        print("\n🎉 所有账号签到成功，无需发送失败通知。")

if __name__ == "__main__":
    # 全局异常捕获
    try:
        main()
    except Exception as e:
        print(f"\n💥 脚本全局异常: {str(e)}")
        if SEND_KEY_LIST:
            send_fail_msg(SEND_KEY_LIST, f"脚本整体崩溃，原因：{str(e)[:80]}")
