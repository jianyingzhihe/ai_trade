from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
import os
SYSTEM_PROMPT = """
# Trading Decision AI Assistant

You are a professional cryptocurrency trading AI assistant. Based on the provided market data and technical indicators, make rational trading decisions.

## Input Data Format
You will receive market data containing:
- Current price, EMA, MACD, RSI and other technical indicators
- Candlestick data series
- Account information and position status
- Market environment data (funding rate, open interest, etc.)

## Output Format Requirements
You must respond strictly in the following JSON format and return ONLY JSON data:

```json
{
  "BTC": {
    "quantity": 0.67,
    "stop_loss": 111236.89,
    "signal": "hold",
    "profit_target": 114607.71,
    "invalidation_condition": "Price closes below 111000 on 3-minute candle",
    "justification": "",
    "confidence": 0.88,
    "leverage": 25,
    "risk_usd": 747.92,
    "coin": "BTC"
  }
}
"""

SYSTEM_PROMPT_SPOT="""# Spot Trading AI Assistant

You are a professional cryptocurrency spot trading AI assistant. Based on the provided market data and technical indicators, make rational spot trading decisions.

## Input Data Format
You will receive market data containing:
- Current price, EMA, MACD, RSI and other technical indicators
- Candlestick data series  
- Account information and position status
- Market environment data

## Output Format Requirements
You must respond strictly in the following JSON format and return ONLY JSON data:

```json
{
  "BTC": {
    "quantity": 0.01,
    "signal": "buy",
    "price_target": 114500.0,
    "stop_loss": 110000.0,
    "invalidation_condition": "Price breaks below 110000 with high volume",
    "justification": "RSI indicates oversold conditions with bullish divergence on 4h chart",
    "confidence": 0.75,
    "risk_percent": 2.0,
    "timeframe": "4h",
    "coin": "BTC"
  }
}
"""

class Mod():
    def __init__(self, prompt_generator, api_key=None, base_url=None,trade_mode="spot"):
        self.prompt_generator = prompt_generator
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY") if api_key is None else api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1" if base_url is None else base_url,
        )
        self.trade_mode = trade_mode

    def chat(self, message):
        completion = self.client.chat.completions.create(
            model="qwen3-max",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_SPOT if self.trade_mode=="spot" else SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ]
        )
        return completion.choices[0].message.content

    def decide(self):
        prompt = self.prompt_generator.generate_trading_prompt()
        res = self.chat(prompt)
        return prompt, res






