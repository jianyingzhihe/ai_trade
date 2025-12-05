import json
import os
import okx.Account as account
import okx.Trade as trade
import okx.Funding as Funding
from dotenv import load_dotenv
import okx.PublicData as PublicData
import okx.MarketData as MarketData

load_dotenv()


class okxbot():
    def __init__(self, is_simu):
        if is_simu:
            self.api_key = os.getenv("OKX_API_KEY_SIMU")
            self.secret_key = os.getenv("OKX_SECRET_KEY_SIMU")
            self.passphrase = os.getenv("OKX_PASSPHRASE")
            self.flag = "1"
        else:
            self.api_key = os.getenv("OKX_API_KEY1")
            self.secret_key = os.getenv("OKX_SECRET_KEY1")
            self.passphrase = os.getenv("OKX_PASSPHRASE1")
            self.flag = "0"
        self.account = account.AccountAPI(self.api_key, self.secret_key, self.passphrase, False, self.flag)
        self.tradeapi = trade.TradeAPI(self.api_key, self.secret_key, self.passphrase, False, self.flag)
        self.publicDataAPI = PublicData.PublicAPI(flag=self.flag)
        self.marketDataAPI = MarketData.MarketAPI(flag=self.flag)
        self.funding=Funding.FundingAPI(self.api_key, self.secret_key, self.passphrase, False, self.flag)

    def execute_decision(self,decision):
        print(decision)
        for coin in decision:
            trade_info=decision[coin]
            instId=(coin+"-USDT").upper()
            if trade_info["signal"]=='buy':
                return self.trade(instId=instId,sz= trade_info["quantity"], side="buy", ordType="market")
            elif trade_info["signal"]=='sell':
                return self.trade(instId=instId,sz= trade_info["quantity"], side="sell", ordType="market")
            elif trade_info["signal"]=='close':
                self.shijiequanping(instId)
            elif trade_info["signal"]=='hole':
                return "waiting"
        # if decision["signal"]=='buy':
        #     self.trade()

    def get_price(self, instId):
        result = self.marketDataAPI.get_ticker(
            instId=instId
        )["data"][0]
        return result

    def get_balance(self, ccy="USDT"):
        """
        获取账户余额
        Args:
            ccy: 币种，默认USDT
        Returns:
            dict: 余额信息
        """
        result = self.account.get_account_balance()

        if result['code'] == '0':
            balance_data = result['data'][0]

            print(f"总权益: {balance_data['totalEq']} USDT")

            if ccy:
                for detail in balance_data['details']:
                    if detail['ccy'] == ccy:
                        print(f"{ccy}余额: 可用={detail['availBal']}, 冻结={detail.get('frozenBal', '0')}")
                        return {
                            'total_eq': balance_data['totalEq'],
                            'available': detail['availBal'],
                            'frozen': detail.get('frozenBal', '0')
                        }
            return {'total_eq': balance_data['totalEq']}
        else:
            print(f"获取余额失败: {result['msg']}")
            return None

    def get_position(self, inst_type="SWAP", inst_id=None):
        """
        获取持仓信息
        Args:
            inst_type: 产品类型
            inst_id: 指定交易对
        Returns:
            list: 持仓列表
        """
        result = self.account.get_positions(instType=inst_type)

        if result['code'] == '0':
            positions = result['data']
            active_positions = []

            for pos in positions:
                print(pos)
                pos_qty = float(pos.get('pos', 0))
                if pos_qty != 0:
                    position_info = {
                        'instId': pos['instId'],
                        'pos': pos['pos'],
                        'posSide': pos['posSide'],
                        'lever': pos['lever'],
                        'avgPx': pos['avgPx'],
                        'markPx': pos.get('markPx', pos.get('last', 'N/A')),
                        'upl': pos['upl'],
                        'uplRatio': pos.get('uplRatio', '0')
                    }
                    active_positions.append(position_info)

                    # 简洁输出
                    print(
                        f"{pos['instId']} {pos['posSide']} {pos['pos']} 杠杆{pos['lever']}x 盈亏{float(pos['upl']):.2f}USDT")

            if not active_positions:
                print("无持仓")

            return active_positions
        else:
            print(f"获取持仓失败: {result['msg']}")
            return None

    def get_position_summary(self):
        """
        获取持仓汇总信息
        Returns:
            dict: 持仓汇总
        """
        positions = self.get_position()
        if not positions:
            return None

        total_upl = 0
        for pos in positions:
            total_upl += float(pos['upl'])

        long_count = len([p for p in positions if p['posSide'] == 'long'])
        short_count = len([p for p in positions if p['posSide'] == 'short'])

        summary = {
            'total_positions': len(positions),
            'total_upl': total_upl,
            'long_count': long_count,
            'short_count': short_count
        }

        print(f"持仓汇总: {len(positions)}个 多{long_count}空{short_count} 总盈亏{total_upl:.2f}USDT")

        return summary

    def shijiequanping(self, instId):
        res = self.tradeapi.close_positions(instId=instId, mgnMode="cash")
        print(res)
        return res

    def trade(self, instId, sz, side, px=None, ordType="market", tdMode="cash",tgtCcy="base_ccy"):
        """

        :param instId:币种
        :param sz: 数量
        :param side: 买或者卖
        :param px: 如果是limit必须填
        :param ordType: 限价或者市价
        :param tdMode: 不用改如果是现货，默认是现金
        :return:
        """
        if ordType=="limit" and px==None:
            return "选了限价单必须填写价格"
        if side != "buy" and side != "sell":
            return "side参数错误，必须是买或者卖"
        res = self.tradeapi.place_order(
            instId=instId,
            side=side,
            # posSide="long",
            tdMode=tdMode,
            px=px,
            sz=sz,
            ordType=ordType,
            tgtCcy=tgtCcy
        )
        print(res)
        return res

    # def trade_spot(self):
    #     res=


    def set_leverage(self, instId, lever, mgnMode, posSide=None):
        """
        设置杠杆倍数
        Args:
            instId: 交易对，如 "BTC-USDT-SWAP"
            lever: 杠杆倍数，如 "10"
            mgnMode: 保证金模式 "cross"全仓 / "isolated"逐仓
            posSide: 持仓方向 (仅在开平仓模式下需要)
                    "long" 多 / "short" 空 / "net" 净持仓
        """
        params = {
            "instId": instId,
            "lever": lever,
            "mgnMode": mgnMode
        }

        # 只有特定模式才需要posSide
        if posSide:
            params["posSide"] = posSide

        result = self.account.set_leverage(**params)

        if result['code'] == '0':
            print(f"设置杠杆成功: {instId} {lever}倍 {mgnMode}模式")
            return result
        else:
            print(f"设置杠杆失败: {result['msg']}")
            return result

    def parse_decision(self, ai_response):
        try:
            import re
            cleaned_response = re.sub(r'```json\s*|\s*```', '', ai_response).strip()
            decision_data = json.loads(cleaned_response)
            return decision_data
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {ai_response}")
            return None
        except Exception as e:
            print(f"Decision parsing error: {e}")
            return None

    def get_coin_kline(self,instId,bar,limit=100):
        """
        获取K线数据
        Args:
            instId: 交易对
            bar: K线粒度
            limit: K线数量
        Returns:
            list: K线数据列表
        """
        return self.marketDataAPI.get_candlesticks(instId=instId,bar=bar,limit=limit)

    def get_coin_num(self):
        """
        获取所有币种的数量
        Returns:
            dict: {币种: 数量}
        """
        result = self.account.get_account_balance()

        if result['code'] != '0':
            print(f"获取余额失败: {result['msg']}")
            return {}

        balance_data = result['data'][0]
        coin_dict = {}

        for detail in balance_data['details']:
            ccy = detail['ccy']
            avail_bal = float(detail['availBal'])
            frozen_bal = float(detail.get('frozenBal', 0))
            total_bal = avail_bal + frozen_bal

            # 只保留有余额的币种
            if total_bal > 0:
                coin_dict[ccy] = total_bal

        # 简洁输出
        print("币种余额:")
        for ccy, amount in coin_dict.items():
            print(f"  {ccy}: {amount}")

        return coin_dict

if __name__ == '__main__':
    testbot = okxbot(True)

    # 测试余额查询
    usdt_balance = testbot.get_balance("USDT")

    # 测试持仓汇总
    # summary = testbot.get_position_summary()
    #
    # testbot.set_leverage("DOGE-USDT-SWAP", 10, "cross", "long")
    # testbot.get_price(instId="DOGE-USDT-SWAP", instType="SWAP")
    # res=testbot.trade("DOGE-USDT",side="sell",sz=631.154, ordType="market")
    # testbot.get_coin_num()
    # print(testbot.get_coin_kline("DOGE-USDT", "1m", 10))
    # res = testbot.shijiequanping("DOGE-USDT-SWAP")
    # res=testbot.shijiequanping("DOGE-USDT-SWAP")