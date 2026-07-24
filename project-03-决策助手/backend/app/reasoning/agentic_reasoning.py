"""Multi-agent reasoning chain: decompose -> execute -> synthesize"""
from app.agents.stock_agent import StockAgent
from app.agents.order_agent import OrderAgent
from app.agents.forecast_agent import ForecastAgent
from app.core.llm import llm


class ReasoningChain:
    def __init__(self):
        self.stock = StockAgent()
        self.order = OrderAgent()
        self.forecast = ForecastAgent()

    def ask(self, question: str) -> dict:
        q = question.lower()
        region = "华东" if "华东" in q else "华南" if "华南" in q else "华北"
        sku = "SKU-AC-001" if "空调" in q else "SKU-FR-001" if "冰箱" in q else ""

        stock = self.stock.query(sku, region)
        transit = self.order.query(sku, region)
        forecast = self.forecast.predict(sku, region)
        recommendation = llm.chat([{"role": "user", "content": question}])

        return {
            "question": question,
            "region": region,
            "data": {"stock": stock, "in_transit": transit, "forecast": forecast},
            "recommendation": recommendation,
            "reasoning_steps": ["stock_query", "order_query", "forecast", "llm_synthesis"],
        }
