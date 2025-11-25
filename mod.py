import asyncio
import websockets
import json
import time
import os
from collections import deque
from openai import OpenAI





async def bitcoin_price_sliding_window():
    uri = "wss://ws.okx.com:8443/ws/v5/public"

    # 滑动窗口：总共200秒数据（20个数据点）
    price_history = deque(maxlen=20)
    analysis_model = Mod()

    # 记录时间控制
    last_record_time = time.time()
    analysis_count = 0

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
        print("启动比特币滑动窗口分析监控")
        print("数据策略: 历史190秒 + 实时10秒滑动窗口")
        print("正在初始化历史数据收集...")

        historical_data_collected = False
        historical_start_time = time.time()

        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                if 'event' in data and data['event'] == 'subscribe':
                    print(f"subscribe successfully: {data['arg']['channel']} - {data['arg']['instId']}")
                    continue

                if 'data' in data and data['data']:
                    current_time = time.time()
                    ticker = data['data'][0]

                    if not historical_data_collected:
                        if current_time - last_record_time >= 10:
                            price_data = create_price_data(ticker, current_time)
                            price_history.append(price_data)
                            last_record_time = current_time

                            elapsed_time = current_time - historical_start_time
                            print(
                                f"[collecting history price] time: {price_data['timestamp']} | price: ${price_data['last_price']} | process: {len(price_history)}/19 | collected: {elapsed_time:.1f}s/190s")

                            if len(price_history) >= 19:
                                historical_data_collected = True
                                print("\n" + "=" * 70)
                                print("finished collecting history price")
                                print("=" * 70 + "\n")

                    else:
                        if current_time - last_record_time >= 10:
                            price_data = create_price_data(ticker, current_time)
                            price_history.append(price_data)
                            last_record_time = current_time
                            analysis_count += 1

                            window_info = analyze_sliding_window(price_history)
                            print(f"time: {price_data['timestamp']} | price: ${price_data['last_price']} | "
                                  f"窗口: {window_info['window_size']}s | 趋势: {window_info['trend']} | "
                                  f"波动: {window_info['volatility']} | 更新: #{analysis_count}")


                            analysis_result = await analyze_sliding_window_data(price_history, analysis_model,
                                                                                analysis_count)
                            print("\nAI res:")
                            print("-" * 50)
                            print(analysis_result)
                            print("-" * 50)


                            await save_sliding_window_data(price_history, analysis_result, analysis_count)
                            print("=" * 70 + "\n")

        except KeyboardInterrupt:
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


def create_price_data(ticker, current_time):
    return {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "unix_timestamp": current_time,
        "trading_pair": ticker.get('instId', 'N/A'),
        "last_price": ticker.get('last', 'N/A'),
        "price_change_percent": ticker.get('last', 'N/A'),
        "high_24h": ticker.get('high24h', 'N/A'),
        "low_24h": ticker.get('low24h', 'N/A'),
        "bid_price": ticker.get('bidPx', 'N/A'),
        "ask_price": ticker.get('askPx', 'N/A'),
        "volume_24h": ticker.get('vol24h', 'N/A'),
        "spread": float(ticker.get('askPx', 0)) - float(ticker.get('bidPx', 0)) if ticker.get('askPx') and ticker.get(
            'bidPx') else 'N/A',
        "data_type": "historical" if len([p for p in locals().get('price_history', [])]) < 19 else "realtime"
    }


async def analyze_sliding_window_data(price_history, model, analysis_count):
    if len(price_history) < 2:
        return "数据不足，等待更多数据点..."

    historical_data = list(price_history)[:-1]
    realtime_data = list(price_history)[-1:]

    total_time_range = price_history[-1]['unix_timestamp'] - price_history[0]['unix_timestamp']
    historical_time_range = historical_data[-1]['unix_timestamp'] - historical_data[0]['unix_timestamp'] if len(
        historical_data) > 1 else 0

    # 准备分析用的数据
    analysis_data = {
        "analysis_id": analysis_count,
        "window_strategy": "历史190秒 + 实时10秒滑动窗口",
        "total_data_points": len(price_history),
        "total_time_range_seconds": total_time_range,
        "historical_context": {
            "data_points": len(historical_data),
            "time_range_seconds": historical_time_range,
            "time_period": "过去190秒",
            "summary_stats": calculate_detailed_stats(historical_data)
        },
        "realtime_update": {
            "data_points": len(realtime_data),
            "time_period": "最近10秒",
            "latest_data": realtime_data[0] if realtime_data else None,
            "change_from_historical": calculate_price_change(historical_data, realtime_data)
        },
        "complete_timeline": {
            "oldest_timestamp": price_history[0]['timestamp'],
            "newest_timestamp": price_history[-1]['timestamp'],
            "price_evolution": track_price_evolution(price_history)
        }
    }

    # 构建详细的prompt
    prompt = f"""
    作为专业的加密货币交易分析师，请基于滑动窗口数据提供分析：

    分析概况：
    - 分析ID: #{analysis_data['analysis_id']}
    - 窗口策略: {analysis_data['window_strategy']}
    - 总数据点: {analysis_data['total_data_points']}个
    - 总时间范围: {analysis_data['total_time_range_seconds']:.1f}秒

    历史上下文（过去190秒）：
    - 数据点: {analysis_data['historical_context']['data_points']}个
    - 时间范围: {analysis_data['historical_context']['time_range_seconds']:.1f}秒
    - 统计摘要: {json.dumps(analysis_data['historical_context']['summary_stats'], indent=2)}

    实时更新（最近10秒）：
    - 最新价格: ${analysis_data['realtime_update']['latest_data']['last_price']}
    - 时间戳: {analysis_data['realtime_update']['latest_data']['timestamp']}
    - 相对于历史的变化: {analysis_data['realtime_update']['change_from_historical']}

    完整时间线：
    - 起始时间: {analysis_data['complete_timeline']['oldest_timestamp']}
    - 结束时间: {analysis_data['complete_timeline']['newest_timestamp']}
    - 价格演变: {analysis_data['complete_timeline']['price_evolution']}

    详细价格历史数据（按时间顺序）：
    {json.dumps(list(price_history), indent=2)}

    请基于以下维度提供深度分析：

    1. 历史趋势分析（190秒窗口）
    2. 实时变化影响（最新10秒）
    3. 趋势延续性或反转信号
    4. 基于历史上下文的实时数据意义
    5. 具体的交易建议（考虑历史模式）
    6. 风险等级评估（结合历史波动）
    7. 支撑阻力位动态更新

    请以以下JSON格式返回分析结果：
    {{
        "analysis_id": {analysis_count},
        "window_strategy": "历史190s + 实时10s",
        "historical_context_summary": "对190秒历史数据的总结",
        "realtime_impact_analysis": "最新10秒数据对趋势的影响",
        "combined_trend_analysis": "结合历史与实时的综合趋势分析",
        "price_momentum": "上涨/下跌/横盘 momentum",
        "trend_strength_with_context": "强/中/弱 (基于历史验证)",
        "volatility_assessment": "高/中/低 (历史对比)",
        "key_support_level": "动态支撑位",
        "key_resistance_level": "动态阻力位", 
        "trading_recommendation": "STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL",
        "recommendation_confidence": "高/中/低",
        "risk_assessment": {{
            "short_term_risk": "高/中/低",
            "historical_consistency": "高/中/低",
            "volatility_risk": "高/中/低"
        }},
        "trading_suggestions": {{
            "entry_point": "建议入场点",
            "stop_loss": "动态止损位", 
            "take_profit": "动态止盈位",
            "position_sizing": "轻仓/标准仓/重仓"
        }},
        "market_behavior_insights": ["洞察1", "洞察2", "洞察3"],
        "next_10s_expectation": "对接下来10秒的预期",
        "reasoning_details": "结合历史与实时的详细推理过程"
    }}

    重点：请特别关注最新10秒数据在190秒历史上下文中的意义和影响。
    """

    try:
        response = model.chat(prompt)
        return response
    except Exception as e:
        return f"AI分析失败: {str(e)}"


def analyze_sliding_window(price_history):
    """实时分析滑动窗口状态"""
    if len(price_history) < 2:
        return {"window_size": 0, "trend": "未知", "volatility": "未知"}

    prices = [float(p['last_price']) for p in price_history if p['last_price'] != 'N/A']
    if len(prices) < 2:
        return {"window_size": 0, "trend": "未知", "volatility": "未知"}

    # 计算窗口大小
    window_seconds = price_history[-1]['unix_timestamp'] - price_history[0]['unix_timestamp']

    # 计算趋势
    price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
    if price_change > 0.1:
        trend = f"↑{price_change:.3f}%"
    elif price_change < -0.1:
        trend = f"↓{abs(price_change):.3f}%"
    else:
        trend = f"→{price_change:.3f}%"

    # 计算波动性
    volatility = calculate_sliding_volatility(prices)

    return {
        "window_size": round(window_seconds),
        "trend": trend,
        "volatility": volatility
    }


def calculate_sliding_volatility(prices):
    """计算滑动窗口波动性"""
    returns = [abs((prices[i] - prices[i - 1]) / prices[i - 1] * 100) for i in range(1, len(prices))]
    avg_volatility = sum(returns) / len(returns) if returns else 0

    if avg_volatility > 0.3:
        return f"高({avg_volatility:.3f}%)"
    elif avg_volatility > 0.1:
        return f"中({avg_volatility:.3f}%)"
    else:
        return f"低({avg_volatility:.3f}%)"


def calculate_detailed_stats(data):
    """计算详细统计信息"""
    prices = [float(p['last_price']) for p in data if p['last_price'] != 'N/A']
    if not prices:
        return {"error": "无有效数据"}

    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)
    price_range = max_price - min_price
    range_percent = (price_range / min_price) * 100

    return {
        "min_price": f"${min_price:.2f}",
        "max_price": f"${max_price:.2f}",
        "avg_price": f"${avg_price:.2f}",
        "price_range": f"${price_range:.2f}",
        "range_percentage": f"{range_percent:.3f}%"
    }


def calculate_price_change(historical_data, realtime_data):
    """计算实时数据相对于历史的变化"""
    if not historical_data or not realtime_data:
        return "数据不足"

    historical_prices = [float(p['last_price']) for p in historical_data if p['last_price'] != 'N/A']
    realtime_price = float(realtime_data[0]['last_price']) if realtime_data[0]['last_price'] != 'N/A' else None

    if not historical_prices or not realtime_price:
        return "数据不足"

    historical_avg = sum(historical_prices) / len(historical_prices)
    change = ((realtime_price - historical_avg) / historical_avg) * 100

    if change > 0:
        return f"高于历史均值 +{change:.3f}%"
    elif change < 0:
        return f"低于历史均值 {change:.3f}%"
    else:
        return "与历史均值持平"


def track_price_evolution(price_history):
    """跟踪价格演变路径"""
    if len(price_history) < 3:
        return "数据点不足"

    segments = []
    for i in range(0, len(price_history), max(1, len(price_history) // 4)):
        if i < len(price_history):
            price = float(price_history[i]['last_price']) if price_history[i]['last_price'] != 'N/A' else 0
            segments.append(f"${price:.2f}")

    return " → ".join(segments)


async def save_sliding_window_data(price_history, analysis_result, analysis_count):
    """保存滑动窗口分析数据"""
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"bitcoin_sliding_window_{timestamp}_analysis{analysis_count}.json"

    data_to_save = {
        "metadata": {
            "analysis_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "analysis_id": analysis_count,
            "window_strategy": "历史190秒 + 实时10秒滑动窗口",
            "total_data_points": len(price_history),
            "total_time_range": price_history[-1]['unix_timestamp'] - price_history[0]['unix_timestamp'],
            "trading_pair": "BTC-USDT"
        },
        "price_history": list(price_history),
        "window_analysis": analyze_sliding_window(price_history),
        "statistical_summary": calculate_detailed_stats(price_history),
        "ai_analysis": analysis_result
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        print(f"滑动窗口分析数据已保存到: {filename}")
    except Exception as e:
        print(f"保存文件失败: {e}")


if __name__ == "__main__":
    print("启动比特币滑动窗口分析监控系统...")
    print("核心策略: 历史190秒数据 + 实时10秒更新")
    print("监控特点:")
    print("- 第一阶段: 收集190秒历史数据建立基准")
    print("- 第二阶段: 每10秒滑动窗口更新和分析")
    print("- 每次分析都包含完整的历史上下文")
    print("- 实时跟踪价格演变和趋势变化")
    print("-" * 60)

    asyncio.run(bitcoin_price_sliding_window())