class DataCollector:
    def __init__(self, okxbot,coin_list, trade_mode="spot"):
        self.data_collectors=[]
        for each in coin_list:
            self.data_collectors.append(TradingDataCollector(okxbot,each,trade_mode))



class TradingDataCollector:
    def __init__(self,okxbot,instId,trade_mode="spot"):
        self.instId=instId
        self.okxbot=okxbot

    def get_price_data(self, bar='3m', limit=50):
        print(f"Requesting {self.instId} K-line data")
        result = self.okxbot.get_coin_kline(self.instId, bar, limit)
        if result and 'data' in result:
            print(f" Successfully retrieved K-line data, total of {len(result['data'])}")
            return self._parse_candle_data(result['data'])
        else:
            print("failed to retrieve K-line data")
            return None

    def _parse_candle_data(self, candle_data):
        candles = []
        for candle in reversed(candle_data):  # 反转数据，从旧到新
            try:
                candles.append({
                    'timestamp': int(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5]),
                    'vol_ccy': float(candle[6])
                })
            except (ValueError, IndexError) as e:
                print(f"Error parsing K-line data: {e}")
                continue
        return candles

    def get_account_info(self):
        result = self.okxbot.account.get_account_balance()
        if result and 'data' in result and result['data']:
            return self._parse_account_data(result['data'][0])
        return None

    def _parse_account_data(self, account_data):
        try:
            print(account_data)
            total_eq = float(account_data.get('totalEq', 0)) if account_data.get('totalEq') else 0
            details = account_data.get('details', [])
            usdt_balance = 0
            instid_balance=0
            for detail in details:
                if detail.get('ccy') == 'USDT':
                    avail_bal = detail.get('availBal', '0')
                    usdt_balance = float(avail_bal) if avail_bal else 0
                if detail.get('ccy') == self.instId.split('-')[0]:
                    avail_bal = detail.get('availBal', '0')
                    instid_balance = float(avail_bal) if avail_bal else 0
            return {
                'total_eq': total_eq,
                'available_cash': usdt_balance,
                'account_value': total_eq,
                self.instId:instid_balance
            }
        except Exception as e:
            print(f"Error parsing account data: {e}")
            return None

    def get_positions(self):
        try:
            result = self.okxbot.account.get_positions()

            if result and 'data' in result:
                all_positions = result['data']
                if all_positions:
                    print(f"✅ 找到 {len(all_positions)} 个持仓")
                    print(all_positions)
                    # 查找当前持仓
                    current_positions = [
                        pos for pos in all_positions
                        if self.instId in pos.get('instId', '') and float(pos.get('pos', 0)) > 0
                    ]
                    if current_positions:
                        print("找到持仓")
                        return self._parse_position_data(current_positions)
                    else:
                        print("没有当前币种持仓")
                        return {self.instId: {'quantity': 0.0}}
                else:
                    print("ℹ️ 账户没有任何持仓")
                    return {'btc_position': {'quantity': 0.0}}
            else:
                print("❌ 持仓查询API失败")
                return {'btc_position': {'quantity': 0.0}}

        except Exception as e:
            print(f"❌ 持仓查询异常: {e}")
            return {'btc_position': {'quantity': 0.0}}

    def _parse_position_data(self, position_data):
        """解析持仓数据 - 增强错误处理"""
        if not position_data:
            return {'btc_position': {'quantity': 0.0}}

        try:
            position = position_data[0]

            return {
                'btc_position': {
                    'symbol': 'BTC',
                    'quantity': float(position.get('pos', 0)),
                    'entry_price': float(position.get('avgPx', 0)),
                    'current_price': float(position.get('markPx', 0)),
                    'liquidation_price': float(position.get('liqPx', 0)),
                    'unrealized_pnl': float(position.get('upl', 0)),
                    'leverage': float(position.get('lever', 1)),
                    'notional_usd': float(position.get('notionalUsd', 0)),
                    'inst_id': position.get('instId', self.instId),
                    'pos_side': position.get('posSide', 'net'),
                    'mgn_mode': position.get('mgnMode', 'isolated')
                }
            }
        except Exception as e:
            print(f"❌ 解析持仓数据错误: {e}")
            return {'btc_position': {'quantity': 0.0}}

    def get_funding_rate(self):
        print("获取资金费率")
        result = self.okxbot.publicDataAPI.get_funding_rate(self.instId)
        if result and 'data' in result and result['data']:
            rate_data = result['data'][0]
            funding_rate = rate_data.get('fundingRate', '0')
            next_funding_rate = rate_data.get('nextFundingRate', '0')
            try:
                funding_rate_float = float(funding_rate) if funding_rate else 0
            except (ValueError, TypeError):
                funding_rate_float = 0
            try:
                next_funding_rate_float = float(next_funding_rate) if next_funding_rate else 0
            except (ValueError, TypeError):
                next_funding_rate_float = 0

            return {
                'rate': funding_rate_float,
                'next_rate': next_funding_rate_float,
                'time': int(rate_data.get('fundingTime', 0))
            }
        return {'rate': 1.25e-05, 'next_rate': 1.25e-05, 'time': 0}

    def get_open_interest(self):
        print("getOpenInterest")
        result = self.okxbot.publicDataAPI.get_open_interest(instId=self.instId)
        if result and 'data' in result and result['data']:
            oi_data = result['data'][0]
            current_oi = float(oi_data.get('oi', 0))
            return {
                'latest': current_oi,
                'average': current_oi
            }
        else:
            print()


import pandas as pd

class TechnicalIndicators:
    @staticmethod
    def calculate_ema(prices, period):
        return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]

    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        series = pd.Series(prices)
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            'macd': macd_line.iloc[-1],
            'signal': signal_line.iloc[-1],
            'histogram': histogram.iloc[-1]
        }

    @staticmethod
    def calculate_rsi(prices, period=14):
        series = pd.Series(prices)
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    @staticmethod
    def calculate_atr(high_prices, low_prices, close_prices, period=14):
        high = pd.Series(high_prices)
        low = pd.Series(low_prices)
        close = pd.Series(close_prices)

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.iloc[-1]
