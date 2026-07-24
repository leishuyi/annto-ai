from app.data.mock_data import WAREHOUSE_STOCK, SALES_HISTORY
class NL2SQL:
    def query(self, question: str) -> dict:
        q = question.lower()
        if "库存" in q: return {"intent":"inventory","sql":"SELECT * FROM stock","results":WAREHOUSE_STOCK[:3],"chart_type":"table"}
        if "销售" in q or "趋势" in q: return {"intent":"sales","sql":"SELECT date,sales FROM sales","results":[{"label":s["date"],"value":s["sales"]} for s in SALES_HISTORY[-7:]],"chart_type":"line"}
        if "准时" in q: return {"intent":"delivery","sql":"SELECT region,rate FROM delivery","results":[{"region":"华东","rate":0.963}],"chart_type":"bar"}
        return {"intent":"unknown","sql":"","results":[],"chart_type":"table"}
