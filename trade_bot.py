import os

from data_collector import *
from okx_trade import *
from model import *
from prompt_generator import *

class TradingBot:

    def __init__(self,coin_list=None, is_simulated=True,trade_mode='spot'):
        if coin_list is None:
            coin_list=["BTC-USDT"]
        self.trading_agent = okxbot(is_simulated)
        self.data_collector =DataCollector(self.trading_agent,coin_list,trade_mode=trade_mode)
        self.prompt_generator = PromptGenerator(self.data_collector)
        self.model = Mod(self.prompt_generator,trade_mode=trade_mode)

    def get_decision(self):
        print("1.AI decision generation in progress...")
        prompt, ai_response = self.model.decide()
        print("2.Parsing trading decision...")
        decision_data = self.trading_agent.parse_decision(ai_response)
        self._save_trading_record(prompt, ai_response, decision_data, True)
        return decision_data

    def run_single_cycle(self):
        try:
            print("1.AI decision generation in progress...")
            prompt, ai_response = self.model.decide()
            print("2.Parsing trading decision...")
            decision_data = self.trading_agent.parse_decision(ai_response)
            if not decision_data:
                print("Decision parsing failed, skipping execution")
                return False
            success = self.trading_agent.execute_decision(decision_data)
            self._save_trading_record(prompt, ai_response, decision_data, success)
            return success
        except Exception as e:
            traceback.print_exc()
            return False

    # def trading_cycle(self):

    def _save_trading_record(self, prompt, ai_response, decision_data, success):
        from datetime import datetime
        import json

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("./trading_record", exist_ok=True)
        filename = f"./trading_record/{timestamp}.json"

        record = {
            'timestamp': timestamp,
            'success': success,
            'decision': decision_data,
            'prompt': prompt,
            'ai_response': ai_response,
            'execution_time': datetime.now().isoformat()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        print(f"record saved at: {filename}")