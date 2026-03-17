import os
import datetime
import requests

# 读取环境变量：与Secrets、YAML名称完全一致
TOKEN_LIST = [t.strip() for t in os.getenv("MILWAUKETOOL_TOKEN_LIST", "").split(",") if t.strip()]
CLIENT_ID_LIST = [c.strip() for c in os.getenv("MILWAUKETOOL_CLIENT_ID", "").split(",") if c.strip()]
SEND_KEY_LIST = [s.strip() for s in os.getenv("SEND_KEY_LIST", "").split(",") if s.strip()]
WEBHOOK_URL = os.getenv("WEBHOOKURL", "")  # 匹配Secrets中的WEBHOOKURL
SERVER_NOTICE_URL = "https://sctapi.ftqq.com/"

def handle_account(token, cid, index):
    """多账号签到核心逻辑"""
    try:
        # 模拟签到请求（替换为真实接口即可）
        resp = requests.get(
            "https://httpbin.org/get",
            params={"token": token, "client_id": cid},
            timeout=10
        )
        resp.raise_for_status()  # 捕获HTTP错误
        msg = f"账号{index} 签到成功"
        print(f"✅ {msg}")
        return True, msg
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") else "未知"
        msg = f"账号{index} 签到失败: HTTP {status_code}"
        print(f"❌ {msg}")
        return False, msg
    except Exception as e:
        msg = f"账号{index} 签到异常: {str(e)[:30]}"
        print(f"⚠️ {msg}")
        return False, msg

def send_server_notice(title, summary, send_key):
    """Server酱通知发送"""
    if not all([send_key, title, summary]):
        print("📤 服务器通知未发送: 缺少关键参数")
        return
    try:
        resp = requests.post(
            f"{SERVER_NOTICE_URL}{send_key}.send",
            data={"title": title, "desp": summary},
            timeout=10
        )
        resp.raise_for_status()
        print("📤 服务器通知发送成功")
    except Exception as e:
        print(f"📤 服务器通知发送失败: {str(e)[:30]}")

def main():
    """主程序：多账号循环+结果汇总"""
    print("====================")
    print("MILWAUKETOOL 多账号签到任务启动")
    print(f"有效账号数: {len(TOKEN_LIST)}")
    print("====================")
    
    # 空账号防护
    if not TOKEN_LIST:
        print("❌ 未配置有效账号，任务终止")
        return
    
    success = 0
    failed = 0
    log_list = []
    
    # 多账号循环签到
    for idx, token in enumerate(TOKEN_LIST):
        cid = CLIENT_ID_LIST[idx] if idx < len(CLIENT_ID_LIST) else ""
        res, msg = handle_account(token, cid, idx + 1)
        log_list.append(msg)
        success += 1 if res else 0
        failed += 1 if not res else 0
    
    # 结果汇总（Markdown格式，适配通知展示）
    title = f"MILWAUKETOOL 签到结果 | 成功{success} 失败{failed}"
    summary = f"""### MILWAUKETOOL 签到任务汇总
**执行时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**账号总数**: {len(TOKEN_LIST)}
**成功数**: {success} | **失败数**: {failed}

### 各账号详细结果
{chr(10).join(log_list)}"""
    
    print("====================")
    print(f"任务结束: 成功{success} | 失败{failed}")
    print("====================")
    
    # 通知发送（无报错取值逻辑）
    print("\n🔔 开始发送通知...")
    send_key = SEND_KEY_LIST[0] if SEND_KEY_LIST else ""
    send_server_notice(title, summary, send_key)

if __name__ == "__main__":
    main()
