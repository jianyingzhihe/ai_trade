import asyncio
import websockets
import json
import time


async def bitcoin_price_monitor():
    """
    使用基础websockets库监控比特币价格
    """
    uri = "wss://ws.okx.com:8443/ws/v5/public"

    async with websockets.connect(uri) as websocket:
        # 订阅比特币价格频道
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "channel": "tickers",
                    "instId": "BTC-USDT"
                }
            ]
        }

        await websocket.send(json.dumps(subscribe_message))
        print("开始订阅比特币价格...")

        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                # 处理订阅成功消息
                if 'event' in data and data['event'] == 'subscribe':
                    print(f"订阅成功: {data['arg']['channel']} - {data['arg']['instId']}")
                    continue

                # 处理ticker数据
                if 'data' in data and data['data']:
                    ticker = data['data'][0]
                    print(f"\n=== 比特币价格更新 ===")
                    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"交易对: {ticker.get('instId', 'N/A')}")
                    print(f"最新价格: ${ticker.get('last', 'N/A')}")
                    print(f"24小时涨跌幅: {ticker.get('last', 'N/A')}%")
                    print(f"24小时最高价: ${ticker.get('high24h', 'N/A')}")
                    print(f"24小时最低价: ${ticker.get('low24h', 'N/A')}")
                    print(f"买一价: ${ticker.get('bidPx', 'N/A')}")
                    print(f"卖一价: ${ticker.get('askPx', 'N/A')}")
                    print(f"24小时成交量: {ticker.get('vol24h', 'N/A')} BTC")
                    print("=" * 30)
                    time.sleep(1)

        except KeyboardInterrupt:
            print("\n收到停止信号，取消订阅...")
            unsubscribe_message = {
                "op": "unsubscribe",
                "args": [
                    {
                        "channel": "tickers",
                        "instId": "BTC-USDT"
                    }
                ]
            }
            await websocket.send(json.dumps(unsubscribe_message))
            print("比特币价格监控已停止")


# 如果你坚持要使用okx库，这里是修正版本
async def bitcoin_price_monitor_okx():
    """
    使用okx库监控比特币价格（修正版本）
    """
    from okx.websocket.WsPublicAsync import WsPublicAsync

    # 修正的初始化方式
    ws = WsPublicAsync(url="wss://ws.okx.com:8443/ws/v5/public")

    def price_callback(message):
        try:
            data = json.loads(message)

            if 'event' in data and data['event'] == 'subscribe':
                print(f"订阅成功: {data['arg']['channel']} - {data['arg']['instId']}")
                return

            if 'data' in data and data['data']:
                ticker = data['data'][0]
                print(f"\n=== 比特币价格更新 ===")
                print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"交易对: {ticker.get('instId', 'N/A')}")
                print(f"最新价格: ${ticker.get('last', 'N/A')}")
                print(f"买一价: ${ticker.get('bidPx', 'N/A')}")
                print(f"卖一价: ${ticker.get('askPx', 'N/A')}")
                print("=" * 30)

        except Exception as e:
            print(f"处理消息时出错: {e}")

    await ws.start()

    subscribe_args = [{
        "channel": "tickers",
        "instId": "BTC-USDT"
    }]

    print("开始订阅比特币价格...")
    await ws.subscribe(subscribe_args, callback=price_callback)

    try:
        print("比特币价格监控已启动，按 Ctrl+C 停止...")
        while True:
            await asyncio.sleep(10)
            print("监控运行中...")

    except KeyboardInterrupt:
        print("\n收到停止信号，取消订阅...")
        await ws.unsubscribe(subscribe_args, callback=price_callback)
        await asyncio.sleep(2)
        print("比特币价格监控已停止")


# 简化的价格监控版本
async def simple_bitcoin_price():
    """
    简化的比特币价格监控 - 使用基础websockets
    """
    uri = "wss://ws.okx.com:8443/ws/v5/public"

    async with websockets.connect(uri) as websocket:
        subscribe_message = {
            "op": "subscribe",
            "args": [
                {
                    "channel": "tickers",
                    "instId": "BTC-USDT"
                }
            ]
        }

        await websocket.send(json.dumps(subscribe_message))
        print("开始监控比特币价格，按 Ctrl+C 停止...")

        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                if 'data' in data and data['data']:
                    ticker = data['data'][0]
                    price = ticker.get('last', 'N/A')
                    if price != 'N/A':
                        print(f"BTC-USDT: ${price} - {time.strftime('%H:%M:%S')}")

        except KeyboardInterrupt:
            print("\n监控已停止")


if __name__ == "__main__":

    print("使用基础websockets库版本...")
    asyncio.run(bitcoin_price_monitor())
