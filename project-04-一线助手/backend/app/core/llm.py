from app.config import settings


class LLMClient:
    def __init__(self):
        self.mock_mode = settings.mock_mode

    def chat(self, messages: list[dict]) -> str:
        if not self.mock_mode:
            raise NotImplementedError("Real LLM mode not configured")
        last = messages[-1]["content"] if messages else ""
        if "差评" in last or "投诉" in last:
            return "建议话术：非常抱歉给您带来不愉快的体验，我们已记录您的问题，将在2小时内由专人跟进处理。为表歉意，我们将为您申请一张20元运费优惠券。"
        if "延迟" in last or "迟到" in last:
            return "建议话术：由于当前路段交通拥堵，您的订单可能会延迟30分钟左右到达，我们已经优先安排配送，感谢您的耐心等待。"
        if "破损" in last or "损坏" in last:
            return "建议话术：非常抱歉商品出现破损，请您拍照留存，我们将立即启动理赔流程，预计48小时内完成赔付。"
        return "建议话术：感谢您的反馈，我已记录您的问题并反馈给相关部门，将在1个工作日内给您答复。"


llm = LLMClient()
