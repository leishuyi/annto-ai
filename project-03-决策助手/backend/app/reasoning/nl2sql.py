"""NL2SQL — 升级为 Schema Linking + Structured Output

优化点：
  - DB Schema 作为固定前缀 → 利用 DeepSeek Prefix Cache
  - 结构化输出约束 SQL 格式
  - 语义缓存同类查询
"""
from app.core.llm_optimizer import NL2SQLEngine, SemanticCache


class NL2SQL:
    """NL2SQL 引擎"""

    def __init__(self):
        self.engine = NL2SQLEngine()
        self.cache = SemanticCache()

    def query(self, question: str) -> dict:
        # 缓存查找
        cached = self.cache.get(question)
        if cached:
            return self._parse_cached(cached)

        # 生成 SQL
        prompt = self.engine.generate_prompt(question)
        sql = self._llm_generate(prompt)

        # 结构化 SQL
        clean_sql = self.engine.parse_sql(sql)

        result = {
            "question": question,
            "sql": clean_sql,
            "results": self._mock_execute(clean_sql),
            "chart_type": self._suggest_chart(question),
        }

        self.cache.set(question, str(result))
        return result

    def _llm_generate(self, prompt: str) -> str:
        """LLM 生成 SQL（生产环境替换为真实 API）"""
        # 当前 mock
        q = prompt.lower()
        if "库存" in q:
            return "SELECT warehouse_id, sku, product_name, quantity FROM inventory WHERE sku = 'SKU-AC-001'"
        if "销售" in q or "趋势" in q:
            return "SELECT date, SUM(quantity) as sales FROM sales WHERE date >= '2026-07-01' GROUP BY date ORDER BY date"
        if "准时" in q:
            return "SELECT region, ROUND(100.0 * on_time / total_orders, 1) as rate FROM delivery WHERE date >= '2026-07-01'"
        return "SELECT 1"

    def _mock_execute(self, sql: str) -> list:
        """Mock 执行（生产环境替换为真实 DB 查询）"""
        from app.data.mock_data import WAREHOUSE_STOCK, SALES_HISTORY
        if "inventory" in sql:
            return WAREHOUSE_STOCK
        if "sales" in sql:
            return [{"date": s["date"], "sales": s["sales"]} for s in SALES_HISTORY[-7:]]
        if "delivery" in sql:
            return [{"region": "华东", "rate": 96.3}]
        return []

    def _suggest_chart(self, question: str) -> str:
        q = question.lower()
        if "趋势" in q or "变化" in q:
            return "line"
        if "库存" in q or "分布" in q:
            return "bar"
        if "占比" in q:
            return "pie"
        return "table"

    def _parse_cached(self, cached: str) -> dict:
        try:
            import ast
            return ast.literal_eval(cached)
        except Exception:
            return {"cached": True, "data": cached}
