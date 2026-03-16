# 强制导入requests（Python3环境，放在脚本最顶部）
import requests
import time
import os

def get_valid_tokens(token_str):
    """过滤空token，返回有效token列表"""
    if not token_str:
        return []
    # 按英文逗号分割，去除首尾空格，过滤空值
    tokens = [token.strip() for token in token_str.split(",") if token.strip()]
    return tokens

def jc_sign_single(token):
    """执行单个嘉立创账号签到（示例逻辑，需匹配真实接口）"""
    try:
        # 替换为嘉立创真实签到接口和请求参数
        sign_url = "https://www.szlcsc.com/api/user/sign/in"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Authorization": f"Bearer {token}"  # 按真实接口的认证方式调整
        }
        # 发送签到请求（GET/POST按接口要求修改）
        response = requests.get(sign_url, headers=headers, timeout=15)
        response.raise_for_status()  # 抛出HTTP状态码错误
        res_data = response.json()
        
        # 按真实接口返回格式判断签到结果
        if res_data.get("code") == 200 or res_data.get("success"):
            return f"签到成功：{res_data.get('msg', '无提示信息')}"
        else:
            return f"签到失败：{res_data.get('msg', '接口返回错误')}"
    except requests.exceptions.RequestException as e:
        return f"网络错误：{str(e)}"
    except Exception as e:
        return f"未知错误：{str(e)}"

def send_server_chan(send_key, content):
    """Server酱通知（可选，适配Python3）"""
    if not send_key:
        return "未配置SendKey，跳过通知"
    try:
        notify_url = f"https://sctapi.ftqq.com/{send_key}.send"
        data = {
            "title": "嘉立创签到结果",
            "desp": content
        }
        response = requests.post(notify_url, data=data, timeout=10)
        response.raise_for_status()
        return "通知发送成功"
    except Exception as e:
        return f"通知发送失败：{str(e)}"

if __name__ == "__main__":
    print("=== 嘉立创自动签到任务启动（Python3）===")
    
    # 从环境变量读取配置
    token_list_str = os.getenv("TOKEN_LIST", "")
    send_key_list_str = os.getenv("SEND_KEY_LIST", "")
    
    # 处理token和sendkey，过滤空值
    valid_tokens = get_valid_tokens(token_list_str)
    valid_send_keys = get_valid_tokens(send_key_list_str)
    
    # 调试输出：查看实际读取的配置
    print(f"读取到有效TOKEN数量：{len(valid_tokens)}")
    print(f"有效TOKEN列表：{valid_tokens}")
    print(f"读取到有效SendKey数量：{len(valid_send_keys)}")
    
    # 无有效token时退出
    if not valid_tokens:
        print("错误：未配置有效TOKEN，任务终止")
        exit(1)
    
    # 遍历执行签到
    sign_results = []
    for index, token in enumerate(valid_tokens, start=1):
        print(f"\n处理第{index}/{len(valid_tokens)}个账号...")
        result = jc_sign_single(token)
        sign_results.append(f"账号{index}：{result}")
        print(f"账号{index}结果：{result}")
        time.sleep(5)  # 避免请求过快触发风控
    
    # 汇总结果并发送通知
    total_result = "\n".join(sign_results)
    print(f"\n=== 签到结果汇总 ===")
    print(total_result)
    
    if valid_send_keys:
        print(f"\n=== 开始发送通知 ===")
        for send_key in valid_send_keys:
            notify_res = send_server_chan(send_key, total_result)
            print(f"SendKey {send_key[-4:]}：{notify_res}")
            time.sleep(2)
    else:
        print("\n未配置有效SendKey，跳过通知步骤")
    
    print("\n=== 嘉立创签到任务执行完毕 ===")
