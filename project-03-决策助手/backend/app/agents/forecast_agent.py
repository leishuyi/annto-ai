from app.data.mock_data import SALES_HISTORY
class ForecastAgent:
    def predict(self, sku: str = "", region: str = "", days: int = 7) -> dict:
        relevant = [s for s in SALES_HISTORY if not region or region in s["region"]]
        avg = sum(s["sales"] for s in relevant[-7:]) / 7 if relevant else 100
        return {"agent":"forecast","avg_daily":round(avg,1),"predicted_7day":round(avg*7,0),"confidence":0.85}
