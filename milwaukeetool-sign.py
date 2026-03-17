import datetime
import requests

# =====================================
# 直接内置测试数据，不依赖任何Secrets
# 完全没有旧名称（MILWAUKEE_TOKEN / MILWAUKETOOL_TOKEN_LIST 都不存在）
# =====================================
TOKEN_LIST = ["test_token_001", "test_token_002", "test_token_003"]
CLIENT_ID_LIST = ["test_cid_001", "test_cid_002", "test_cid_003"]
SEND_KEY_LIST = [""]

# =====================================
# 模拟签到请求，可替换为真实接口
# =====================================
def handle_account(token, cid, index):
    try:
        resp = requests.get(
            "https://httpbin.org/get",
            params={"token": token, "client_id": cid},
            timeout=10
        )
        resp.raise_for_status()
        return True, f"账号{index} 签到成功 ✅"
    except Exception as e:
        return False, f"账号{index} 签到失败 ❌"

# =====================================
# 通知功能（不填key也不会失败）
# =====================================
def send_notice(title, content, key):
    if not key:
        print("(未配置Send Key，跳过通知)")
        return
    try:
        requests.post(
            f"https://sctapi.ftqq.com/{key}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        print("通知发送成功")
    except:
        print("通知发送失败")

# =====================================
# 主程序（完全简化，无复杂逻辑）
# =====================================
def main():
    print("====================")
    print("MILWAUKETOOL 多账号签到启动")
    print(f"有效账号数: {len(TOKEN_LIST)}")
    print("====================")

    success, failed, logs = 0, 0, []

    for idx, token in enumerate(TOKEN_LIST):
        cid = CLIENT_ID_LIST[idx] if idx < len(CLIENT_ID_LIST) else ""
        res, msg = handle_account(token, cid, idx + 1)
        logs.append(msg)
        success += 1 if res else 0
        failed += 1 if not res else 0

    summary = f"""
MILWAUKETOOL 签到汇总
时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总数: {len(TOKEN_LIST)} | 成功: {success} | 失败: {failed}

详细:
{chr(10).join(logs)}
    """

    print(summary)
    send_notice(f"签到结果：成功{success}", summary, SEND_KEY_LIST[0] if SEND_KEY_LIST else "")

if __name__ == "__main__":
    main()
