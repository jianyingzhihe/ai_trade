import os
import requests
import json
import hmac
import base64
from datetime import datetime, timezone

# 配置
API_KEY = os.getenv("OKX_API_KEY_SIMU")
SECRET_KEY = os.getenv("OKX_SECRET_KEY_SIMU")
PASSPHRASE = os.getenv("OKX_PASSPHRASE")
BASE_URL = "https://www.okx.com"


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()[:-9] + 'Z'


def sign(timestamp, method, request_path, secret_key, body=''):
    message = timestamp + method.upper() + request_path + body
    mac = hmac.new(
        bytes(secret_key, encoding='utf-8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    return base64.b64encode(mac.digest()).decode()


def make_request(method, endpoint, params=None):
    timestamp = get_timestamp()
    body = json.dumps(params) if params else ''
    signature = sign(timestamp, method, endpoint, SECRET_KEY, body)

    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json',
        'x-simulated-trading': '1'
    }

    url = BASE_URL + endpoint

    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, data=body, timeout=10)

        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"请求错误: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应内容: {e.response.text}")
        return None


def set_account_level(acct_lv):
    """设置账户模式"""
    print(f"🔄 设置账户模式为: {acct_lv}")

    endpoint = "/api/v5/account/set-account-level"
    params = {
        'acctLv': str(acct_lv)  # 1:现货, 2:合约, 3:跨币种, 4:组合
    }

    result = make_request('POST', endpoint, params)
    print(f"设置结果: {result}")

    if result and result.get('code') == '0':
        print(f"✅ 账户模式设置成功: {acct_lv}")
        return True
    else:
        print(f"❌ 账户模式设置失败")
        return False


def check_current_account_level():
    """检查当前账户模式"""
    print("🔍 检查当前账户模式...")

    result = make_request('GET', '/api/v5/account/config')
    if result and 'data' in result and result['data']:
        account_config = result['data'][0]
        current_level = account_config.get('acctLv')
        print(f"当前账户模式: {current_level}")

        level_names = {
            '1': '简单交易模式',
            '2': '单币种保证金模式',
            '3': '跨币种保证金模式',
            '4': '组合保证金模式'
        }

        print(f"模式说明: {level_names.get(current_level, '未知')}")
        return current_level
    return None


def main():
    print("=" * 50)
    print("OKX 账户模式设置")
    print("=" * 50)

    # 检查当前模式
    current_level = check_current_account_level()

    if current_level == '1':
        print("\n🚨 当前是简单交易模式，需要切换到合约模式")

        # 尝试切换到合约模式
        print("\n尝试切换到合约模式...")
        success = set_account_level(2)  # 2 = 合约模式

        if success:
            print("\n🎉 切换成功! 现在可以测试合约交易了")

            # 测试下单
            print("\n🧪 测试下单...")
            test_order()
        else:
            print("\n❌ 切换失败，可能需要:")
            print("1. 平掉所有仓位")
            print("2. 在网页端手动切换")
            print("3. 联系客服")

    elif current_level in ['2', '3', '4']:
        print(f"\n✅ 当前已经是合约支持模式 (级别: {current_level})")
        print("可以直接测试合约交易!")

        # 直接测试下单
        test_order()


def test_order():
    """测试合约下单"""
    print("\n📈 测试合约下单...")

    # 先设置仓位模式
    print("1. 设置仓位模式...")
    result = make_request('POST', '/api/v5/account/set-position-mode', {
        'posMode': 'long_short_mode'
    })
    print(f"   仓位模式设置: {result}")

    # 尝试下单
    print("2. 尝试下单...")
    order_result = make_request('POST', '/api/v5/trade/order', {
        'instId': 'BTC-USDT-SWAP',
        'tdMode': 'isolated',
        'side': 'buy',
        'ordType': 'market',
        'sz': '0.01'
    })

    print(f"   下单结果: {order_result}")

    if order_result and order_result.get('code') == '0':
        print("🎉 合约交易测试成功!")
    else:
        print("❌ 合约交易测试失败")


if __name__ == "__main__":
    main()