"""Script assistant — 话术助手

优化点：
  1. 双路情绪识别（关键词 + LLM 回退）
  2. 场景化提示词模板（Prefix Cache 友好）
  3. 本地响应缓存（离线可用）
"""
from app.schemas.driver import ScriptRequest, ScriptResponse
from app.core.llm_optimizer import ScenePrompts, SentimentAnalyzer, LocalResponseCache


# 预编译场景提示词模板
_prompts = ScenePrompts()
_analyzer = SentimentAnalyzer(llm_callback=None)
_cache = LocalResponseCache()


def get_script(req: ScriptRequest) -> ScriptResponse:
    # 1. 本地缓存查找
    cache_key = f"script:{req.customer_query}"
    cached = _cache.get(cache_key)
    if cached:
        return _parse_cached(cached, req.customer_query)

    # 2. 双路情绪识别
    sentiment = _analyzer.analyze(req.customer_query)

    # 3. 构建提示词
    prompt = _prompts.SCRIPT.format(
        sentiment=sentiment.sentiment,
        query=req.customer_query,
    )
    response = _call_llm(prompt)

    result = ScriptResponse(
        suggested_response=response,
        sentiment=sentiment.sentiment,
    )

    # 4. 写入缓存
    _cache.set(cache_key, str(result.model_dump()))

    return result


def _call_llm(prompt: str) -> str:
    """LLM 调用（生产环境替换为真实 DeepSeek API）"""
    # 当前 mock
    return "您好，我已收到您的反馈。我们会尽快核实并处理，请保持电话畅通。"


def _parse_cached(cached: str, default_query: str) -> ScriptResponse:
    try:
        import ast
        data = ast.literal_eval(cached)
        return ScriptResponse(**data)
    except Exception:
        return ScriptResponse(suggested_response=cached, sentiment="neutral")
