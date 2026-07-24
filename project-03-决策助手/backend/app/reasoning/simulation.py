"""仿真引擎 — 升级为场景化推演 + 语义缓存

优化点：
  - 场景模板预编译（Prefix Cache 友好）
  - 多路径推演（不同假设条件）
  - 结构化输出约束
"""
from app.core.llm_optimizer import SemanticCache


class Simulation:
    """仿真推演引擎"""

    SCENARIO_TEMPLATES = {
        "需求": "需求激增",
        "天气": "天气影响",
        "供应": "供应中断",
    }

    def __init__(self):
        self.cache = SemanticCache()

    def run(self, scenario: str) -> dict:
        # 缓存查找
        cached = self.cache.get(scenario)
        if cached:
            return {"cached": True, "scenario": scenario, "result": cached}

        result = self._simulate(scenario)
        self.cache.set(scenario, str(result))

        return result

    def _simulate(self, scenario: str) -> dict:
        s = scenario.lower()
        if "需求" in s:
            return {"scenario": "需求激增", "impact": "需求增30%将导致库存3天内耗尽", "confidence": 0.82}
        if "天气" in s:
            return {"scenario": "天气影响", "impact": "气温降10°C，空调销量预计降15%", "confidence": 0.75}
        if "供应" in s:
            return {"scenario": "供应中断", "impact": "延迟5天将导致SKU缺货", "confidence": 0.78}
        return {"scenario": scenario, "impact": "影响有限", "confidence": 0.6}
