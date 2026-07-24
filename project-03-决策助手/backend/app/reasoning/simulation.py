class Simulation:
    def run(self, scenario: str) -> dict:
        s = scenario.lower()
        if "需求" in s: return {"scenario":"需求激增","impact":"需求增30%将导致库存3天内耗尽","confidence":0.82}
        if "天气" in s: return {"scenario":"天气影响","impact":"气温降10C，空调销量预计降15%","confidence":0.75}
        if "供应" in s: return {"scenario":"供应中断","impact":"延迟5天将导致SKU缺货","confidence":0.78}
        return {"scenario":scenario,"impact":"影响有限","confidence":0.6}
