import requests
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path

# ================= 配置区 =================
CONFIG_FILE = "accounts.json"  # 账号配置文件名

SECRET = "36affdc58f50e1035649abc808c22b48"
APPKEY = "76472358"
PLATFORM = "MP-WEIXIN"
FORMAT = "json"
URL = "https://service.milwaukeetool.cn/api/v1/user"

HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254173b) XWEB/19027",
    'Content-Type': "application/json",
    'xweb_xhr': "1",
    'Sec-Fetch-Site': "cross-site",
    'Sec-Fetch-Mode': "cors",
    'Sec-Fetch-Dest': "empty",
    'Referer': "https://servicewechat.com/wxc13e77b0a12aac68/59/page-frame.html",
    'Accept-Language': "zh-CN,zh;q=0.9"
}


# ================= 核心功能函数 =================

def generate_sign(params_dict):
    """生成签名"""
    sorted_keys = sorted(params_dict.keys())
    s = SECRET
    for key in sorted_keys:
        val = params_dict[key]
        if isinstance(val, bool):
            val = 1 if val else 0
        s += str(key) + str(val)
    s += SECRET
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def check_single_account(account_info, index, total):
    """
    处理单个账号的查询逻辑
    """
    name = account_info.get("name", f"账号_{index}")
    token = account_info.get("token")
    client_id = account_info.get("client_id")

    print(f"\n[{index}/{total}] 正在查询: {name} (ID: {client_id})")

    if not token or not client_id:
        print(f"   ❌ 跳过: 缺少 token 或 client_id")
        return None

    # 1. 准备数据
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "token": token,
        "client_id": client_id,
        "appkey": APPKEY,
        "format": FORMAT,
        "timestamp": timestamp_str,
        "platform": PLATFORM,
        "method": "get.user.item"
    }

    # 2. 计算签名
    payload["sign"] = generate_sign(payload)

    # 3. 发送请求
    try:
        response = requests.post(URL, data=json.dumps(payload), headers=HEADERS, timeout=10)
        response.raise_for_status()
        resp_json = response.json()

        # 4. 提取积分 (核心逻辑)
        # 路径: data -> get_user_money -> points
        data_node = resp_json.get("data", {})
        money_node = data_node.get("get_user_money", {})
        points = money_node.get("points")

        # 顺便提取其他信息
        mobile = data_node.get("mobile", "未知")
        status_code = resp_json.get("status") or resp_json.get("code")

        # 5. 判断结果
        if points is not None:
            print(f"   ✅ 成功 | 积分: {points} | 手机: {mobile}")
            return {"name": name, "points": points, "status": "success"}
        else:
            # 如果 points 是 None，可能是业务错误
            msg = resp_json.get("message") or resp_json.get("msg") or "未知错误"
            print(f"   ⚠️ 失败 | 原因: {msg} (返回数据中无积分字段)")
            return {"name": name, "points": 0, "status": "failed", "reason": msg}

    except requests.exceptions.RequestException as e:
        print(f"   ❌ 网络错误: {str(e)}")
        return {"name": name, "points": 0, "status": "error", "reason": str(e)}
    except Exception as e:
        print(f"   ❌ 系统错误: {str(e)}")
        return {"name": name, "points": 0, "status": "error", "reason": str(e)}


def main():
    print("=" * 50)
    print("🚀 美沃奇积分批量查询工具")
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. 检查并读取配置文件
    if not Path(CONFIG_FILE).exists():
        print(f"\n❌ 错误: 未找到 '{CONFIG_FILE}' 文件！")
        print("请确保该文件与脚本在同一目录下。")
        return

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
    except json.JSONDecodeError:
        print(f"\n❌ 错误: '{CONFIG_FILE}' 文件格式不正确，请检查 JSON 语法。")
        return
    except Exception as e:
        print(f"\n❌ 读取文件失败: {e}")
        return

    if not isinstance(accounts, list) or len(accounts) == 0:
        print("\n❌ 账号列表为空。")
        return

    print(f"📂 共发现 {len(accounts)} 个账号，开始执行...\n")

    # 2. 批量执行
    results = []
    total_points = 0

    for i, acc in enumerate(accounts, 1):
        # 可选：添加短暂延时，避免触发频率限制
        if i > 1:
            time.sleep(1)

        res = check_single_account(acc, i, len(accounts))
        if res:
            results.append(res)
            if res["status"] == "success":
                total_points += res["points"]

    # 3. 输出汇总报告
    print("\n" + "=" * 50)
    print("📊 查询结果汇总")
    print("=" * 50)

    success_count = sum(1 for r in results if r["status"] == "success")
    fail_count = len(results) - success_count

    print(f"✅ 成功: {success_count} 个")
    print(f"❌ 失败: {fail_count} 个")
    print(f"💰 总积分: {total_points}")

    if success_count > 0:
        print("\n📋 详情列表:")
        for r in results:
            if r["status"] == "success":
                print(f"   • {r['name']}: {r['points']} 分")
            else:
                print(f"   • {r['name']}: 失败 ({r.get('reason', '未知')})")

    print("=" * 50)


if __name__ == "__main__":
    main()