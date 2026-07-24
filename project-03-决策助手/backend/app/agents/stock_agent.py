from app.data.mock_data import WAREHOUSE_STOCK
class StockAgent:
    def query(self, sku: str = "", region: str = "") -> dict:
        results = [s for s in WAREHOUSE_STOCK if (not sku or sku in s["sku"]) and (not region or region in s["warehouse_id"])]
        return {"agent":"stock","results":results,"total":sum(r["qty"] for r in results)}
