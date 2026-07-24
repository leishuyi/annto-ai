from app.config import settings
class LLMClient:
    def __init__(self):
        self.mock_mode = settings.mock_mode
    def chat(self, messages: list[dict]) -> str:
        if not self.mock_mode:
            raise NotImplementedError("Real LLM not configured")
        q = messages[-1]["content"] if messages else ""
        if "补货" in q:
            return "建议：华东区库存2500台，在途500台，日均销售120台，建议补货2000台"
        if "准时" in q:
            return "华东区7月配送准时率96.3%，目标95%，表现达标"
        return f"已分析：{q[:30]}... 建议保持现有节奏"
llm = LLMClient()
