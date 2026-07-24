"""LLM 客户端 — 始终安全回退到 mock 模式。"""
from loguru import logger


class LLMClient:
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode

    def chat(self, messages: list[dict]) -> str:
        try:
            if not self.mock_mode:
                from app.config import settings
                if settings.llm_api_key:
            # TODO: 接入真实 DeepSeek API
            # 当前 mock 占位：在 settings.llm_api_key 配置完成前，所有 LLM 调用走 fallback
            # 接入后移除这里的 raise，改为真实的 openai.ChatCompletion.create
                    pass
            raise NotImplementedError("LLM API not connected")
        except Exception as e:
            logger.warning("LLM 调用失败，使用 mock 回退", error=str(e))
            return self._mock_response(messages)

    def _mock_response(self, messages: list[dict]) -> str:
        q = messages[-1]["content"] if messages else ""
        if "补货" in q:
            return "建议：华东区库存2500台，在途500台，日均销售120台，建议补货2000台"
        if "准时" in q:
            return "华东区7月配送准时率96.3%，目标95%，表现达标"
        return f"已分析：{q[:30]}... 建议保持现有节奏"


llm = LLMClient()
