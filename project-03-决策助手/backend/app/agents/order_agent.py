from app.data.mock_data import IN_TRANSIT
class OrderAgent:
    def query(self, sku: str = "", region: str = "") -> dict:
        results = [o for o in IN_TRANSIT if not sku or sku in o["sku"]]
        return {"agent":"order","results":results,"total":sum(r["qty"] for r in results)}
