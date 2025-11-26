import traceback
from datetime import datetime
import numpy as np
import time
from data_collector import *

class PromptGenerator:
    def __init__(self, data_collector,trade_mode="spot"):
        self.data_collector = data_collector
        self.start_time = time.time()
        self.invocation_count = 0
        self.trade_mode=trade_mode
        self.indicators = TechnicalIndicators()

    def generate_coin_data(self,data_collector):
        print("collection market data...")
        price_data_3m = data_collector.get_price_data('3m', 50)
        price_data_4h = data_collector.get_price_data('4H', 50)
        account_info = data_collector.get_account_info()
        account_balance=account_info[data_collector.instId]
        positions = data_collector.get_positions()

        funding_rate = data_collector.get_funding_rate()

        open_interest = data_collector.get_open_interest() if self.trade_mode == "swap" else 0

        indicators_3m = self._calculate_indicators(price_data_3m)
        indicators_4h = self._calculate_indicators_4h(price_data_4h)


        coin_prompt=f"""ALL {data_collector.instId} DATA
current_price = {indicators_3m['current_price']}, current_ema20 = {indicators_3m['ema20']:.3f}, current_macd = {indicators_3m['macd']:.3f}, current_rsi (7 period) = {indicators_3m['rsi7']:.2f}

In addition, here is the latest coin open interest and funding rate for perps (the instrument you are trading):"""
        if self.trade_mode == "swap":
            coin_prompt+=f"""Open Interest: Latest: {open_interest['latest']:.1f} Average: {open_interest['average']:.2f}"""
        coin_prompt+=f"""Funding Rate: {funding_rate['rate']:.5f}

Intraday series (by minute, oldest → latest):

Mid prices: {indicators_3m['mid_prices']}

EMA indicators (20‑period): {indicators_3m['ema_series']}

MACD indicators: {indicators_3m['macd_series']}

RSI indicators (7‑Period): {indicators_3m['rsi7_series']}

RSI indicators (14‑Period): {indicators_3m['rsi14_series']}

Longer‑term context (4‑hour timeframe):

20‑Period EMA: {indicators_4h['ema20_4h']:.3f} vs. 50‑Period EMA: {indicators_4h['ema50_4h']:.3f}

3‑Period ATR: {indicators_4h['atr3']:.3f} vs. 14‑Period ATR: {indicators_4h['atr14']:.3f}

Current Volume: {indicators_4h['current_volume']:.3f} vs. Average Volume: {indicators_4h['avg_volume']:.3f}

MACD indicators: {indicators_4h['macd_4h_series']}

RSI indicators (14‑Period): {indicators_4h['rsi14_4h_series']}

HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE

Available Cash: {account_info.get('available_cash', 15581.17):.2f}

Current Account Value: {account_info.get('account_value', 19527.81):.2f}\n"""

        if self.trade_mode == "swap":
            coin_prompt+=f"""Current live positions & performance: {str(positions)}"""
        else:
            coin_prompt+=f"""Current coin balance & performance: {data_collector.instId} Balance: {account_balance} """

        return coin_prompt


    def generate_trading_prompt(self):
        self.invocation_count += 1
        print("collection market data...")
        minutes_running = int((time.time() - self.start_time) / 60)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        prompt = f"""It has been {minutes_running} minutes since you started trading. The current time is {current_time} and you've been invoked {self.invocation_count} times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha. Below that is your current account information, value, performance, positions, etc.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

Timeframes note: Unless stated otherwise in a section title, intraday series are provided at 3‑minute intervals. If a coin uses a different interval, it is explicitly stated in that coin’s section.

CURRENT MARKET STATE FOR ALL COINS\n"""
        for each in self.data_collector.data_collectors:
            prompt+=self.generate_coin_data(each)
        return prompt


    def _calculate_indicators(self, price_data):
        if not price_data or len(price_data) < 30:
            print(f"Insufficient data, at least 30 entries are required, currently only {len(price_data) if price_data else 0}条")


        try:
            closes = [candle['close'] for candle in price_data]
            highs = [candle['high'] for candle in price_data]
            lows = [candle['low'] for candle in price_data]

            current_price = float(closes[-1])

            # calculate indicators
            ema20 = float(self.indicators.calculate_ema(closes, 20))
            macd_data = self.indicators.calculate_macd(closes)
            macd_current = float(macd_data['macd'])
            rsi7 = float(self.indicators.calculate_rsi(closes, 7))
            rsi14 = float(self.indicators.calculate_rsi(closes, 14))

            mid_prices = [float(round(candle['close'], 1)) for candle in price_data[-10:]]

            ema_series = []
            for i in range(20, len(closes)):
                ema_value = self.indicators.calculate_ema(closes[:i + 1], 20)
                ema_series.append(float(round(ema_value, 3)))
            ema_series = ema_series[-10:] if len(ema_series) >= 10 else ema_series

            macd_series = []
            for i in range(26, len(closes)):
                macd_value = self.indicators.calculate_macd(closes[:i + 1])['macd']
                macd_series.append(float(round(macd_value, 3)))
            macd_series = macd_series[-10:] if len(macd_series) >= 10 else macd_series

            rsi7_series = []
            for i in range(14, len(closes)):
                # Use a fixed-length window: take the most recent 14 price points
                window_data = closes[i - 13:i + 1]
                rsi_value = self.indicators.calculate_rsi(window_data, 7)
                rsi7_series.append(float(round(rsi_value, 2)))

            rsi7_series = rsi7_series[-10:] if len(rsi7_series) >= 10 else rsi7_series

            rsi14_series = []
            for i in range(14, len(closes)):
                rsi_value = self.indicators.calculate_rsi(closes[:i + 1], 14)
                rsi14_series.append(float(round(rsi_value, 2)))
            rsi14_series = rsi14_series[-10:] if len(rsi14_series) >= 10 else rsi14_series

            # If the series data is empty, fill with the current value
            if not macd_series:
                macd_series = [float(round(macd_current, 3))] * min(10, len(closes))
            if not ema_series:
                ema_series = [float(round(ema20, 3))] * min(10, len(closes))
            if not rsi7_series:
                rsi7_series = [float(round(rsi7, 2))] * min(10, len(closes))
            if not rsi14_series:
                rsi14_series = [float(round(rsi14, 2))] * min(10, len(closes))

            print(f"Indicator calculation completed: Price={current_price:.6f}, EMA20={ema20:.3f}, MACD={macd_current:.3f}")
            print(f"Data length - Price:{len(closes)}, EMA:{len(ema_series)}, MACD:{len(macd_series)}")

            return {
                'current_price': current_price,
                'ema20': ema20,
                'macd': macd_current,
                'rsi7': rsi7,
                'rsi14': rsi14,
                'mid_prices': mid_prices,
                'ema_series': ema_series,
                'macd_series': macd_series,
                'rsi7_series': rsi7_series,
                'rsi14_series': rsi14_series
            }

        except Exception as e:
            traceback.print_exc()

    def _calculate_indicators_4h(self, price_data):
        if not price_data or len(price_data) < 30:
            print(f"Insufficient data, at least 30 entries are required, currently only {len(price_data) if price_data else 0}")

        try:
            closes = [candle['close'] for candle in price_data]
            highs = [candle['high'] for candle in price_data]
            lows = [candle['low'] for candle in price_data]
            volumes = [candle['volume'] for candle in price_data]

            ema20_4h = float(self.indicators.calculate_ema(closes, 20))
            ema50_4h = float(self.indicators.calculate_ema(closes, 50))


            atr3 = float(self.indicators.calculate_atr(highs[-3:], lows[-3:], closes[-3:], 3))
            atr14 = float(self.indicators.calculate_atr(highs, lows, closes, 14))

            macd_4h_series = []
            for i in range(26, len(closes)):
                macd_value = self.indicators.calculate_macd(closes[:i + 1])['macd']
                macd_4h_series.append(float(round(macd_value, 3)))
            macd_4h_series = macd_4h_series[-10:] if len(macd_4h_series) >= 10 else macd_4h_series

            rsi14_4h_series = []
            for i in range(14, len(closes)):
                rsi_value = self.indicators.calculate_rsi(closes[:i + 1], 14)
                rsi14_4h_series.append(float(round(rsi_value, 3)))
            rsi14_4h_series = rsi14_4h_series[-10:] if len(rsi14_4h_series) >= 10 else rsi14_4h_series

            if not macd_4h_series:
                current_macd = float(self.indicators.calculate_macd(closes)['macd'])
                macd_4h_series = [float(round(current_macd, 3))] * min(10, len(closes))

            if not rsi14_4h_series:
                current_rsi = float(self.indicators.calculate_rsi(closes, 14))
                rsi14_4h_series = [float(round(current_rsi, 3))] * min(10, len(closes))

            return {
                'ema20_4h': ema20_4h,
                'ema50_4h': ema50_4h,
                'atr3': atr3,
                'atr14': atr14,
                'current_volume': float(volumes[-1]) if volumes else 0.0,
                'avg_volume': float(np.mean(volumes)) if volumes else 0.0,
                'macd_4h_series': macd_4h_series,
                'rsi14_4h_series': rsi14_4h_series
            }

        except Exception as e:
            print("4H calc error:")
