import os
import datetime
import requests

# =====================================
# 【关键恢复】这里重新读取 GitHub Secrets 的变量
# 名字与你截图里的 Secrets 完全对应：
# MILWAUKETOOL_TOKEN_LIST
# MILWAUKETOOL_CLIENT_ID
# SEND_KEY_LIST
# =====================================
TOKEN_LIST = [t.strip() for t in os.getenv("MILWAUKETOOL_TOKEN_LIST", "").split(",") if t.strip()]
CLIENT_ID_LIST = [c.strip() for c in os.getenv("MILWAUKETOOL_CLIENT_ID", "").split(",") if c.strip()]
SEND_KEY_LIST = [s.strip() for s in os.getenv("SEND_KEY_LIST", "").split(",") if s.strip()]

# 兼容你可能只有1个账号的情况
if len(CLIENT_ID_LIST) < len(TOKEN_LIST):
    CLIENT_ID_LIST += [""] * (len(TOKEN_LIST) - len(CLIENT_ID_LIST))

SERVER_NOTICE_URL = "https://sctapi.ftqq.com/"

# =====================================
# 真实签到逻辑（这里你可以换成真实接口）
# =====================================
def handle_account(token, cid, index):
    try:
        # 这里目前是模拟逻辑，你可以把地址改成真实的签到地址
        # 示例：resp = requests.get("https://真实接口地址.com", params={"token": token, "client_id": cid})
        resp = requests.get("https://httpbin.org/get", params={"token": token, "client_id": cid}, timeout=10)
        
        # 这里可以根据返回状态码判断是否签到成功
        # 假设 200 是成功，4xx 是重复签到或失败
        if resp.status_code == 200:
            return True, f"账号{index} 签到成功 ✅"
        elif resp.status_code == 409: # 假设409是重复签到
            return False, f"账号{index} 今日已签到 🈲"
        else:
            return False, f"账号{index} 签到失败 ❌"
    except Exception as e:
        return False, f"账号{index} 异常 ❌ ({str(e)[:10]})"

def main():
    print("====================")
    print("MILWAUKETOOL 签到任务")
    print(f"有效账号数: {len(TOKEN_LIST)}")
    print("====================")

    if not TOKEN_LIST:
        print("❌ 未检测到账号，请检查 Secrets 配置")
        return

    success, failed, logs = 0, 0, []
    
    # 循环执行
    for idx in range(len(TOKEN_LIST)):
        token = TOKEN_LIST[idx]
        cid = CLIENT_ID_LIST[idx] if idx < len(CLIENT_ID_LIST) else ""
        res, msg = handle_account(token, cid, idx + 1)
        logs.append(msg)
        if res:
            success += 1
        else:
            failed += 1

    # 汇总
    summary = f"""
    MILWAUKETOOL 签到汇总
    时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    总数: {len(TOKEN_LIST)} | 成功: {success} | 失败: {failed}
    
    详细:
    {chr(10).join(logs)}
    """
    print(summary)

    # 发送通知
    if SEND_KEY_LIST:
        try:
            requests.post(f"{SERVER_NOTICE_URL}{SEND_KEY_LIST[0]}.send", 
                          data={"title": f"签到结果: {success}成功/{failed}失败", "desp": summary})
        except:
            pass

if __name__ == "__main__":
    main()
