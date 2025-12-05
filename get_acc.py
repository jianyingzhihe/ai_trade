from okx_trade import *
if __name__ == '__main__':
    testbot = okxbot(True)
    # 测试余额查询

    usdt_balance = testbot.get_balance("USDT")
    print(usdt_balance)