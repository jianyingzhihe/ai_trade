from trade_bot import *

# 使用示例
if __name__ == "__main__":
    # 创建交易机器人（模拟交易）
    bot = TradingBot(is_simulated=True,coin_list=["DOGE-USDT"])
    # success = bot.get_decision()
    bot.trading_cycle()
