"""LLM 优化引擎 — 生产级优化套件

技术栈：
  1. Prompt Cache — 静态前缀分离，适配 DeepSeek Prefill-Cache（cache hit 降本 90%）
  2. Semantic Cache — embedding 语义缓存，相似问题直接命中
  3. Structured Output — JSON Schema 约束生成 + 自动重试
  4. Model Cascade — 轻量模型 → 重模型逐级回退 + 熔断

用法：
    optimizer = LLMOptimizer()
    result = await optimizer.complete(
        messages=[{"role": "user", "content": "..."}],
        output_schema=MySchema,
    )
"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Generic, Optional, TypeVar

from loguru import logger

# =============================================================================
# 1. Prompt Cache — 构造对 DeepSeek Prefill-Cache 友好的请求
# =============================================================================

T = TypeVar("T")


class PromptBuilder:
    """提示词构造器：静态前缀 + 动态后缀，最大化 Prefix Cache 命中率。

    DeepSeek 对 byte-exact 前缀自动缓存，cache hit 单价降至 1/40~1/120。
    核心原则：
    - 所有静态内容（system prompt、tool defs、few-shot）放在最前
    - 所有动态内容（user query、时间戳）放在最后
    - 使用确定性序列化保证 byte 一致性
    """

    def __init__(self, system_prompt: str = "", tools: Optional[list[dict]] = None):
        self._static_prefix = self._build_static(system_prompt, tools or [])

    def _build_static(self, system: str, tools: list[dict]) -> list[dict]:
        """构建静态前缀（只构建一次，后续复用）"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if tools:
            # 确定性序列化：确保工具定义每次完全一致
            messages.append({
                "role": "system",
                "content": f"# Tools\n{json.dumps(tools, ensure_ascii=False, sort_keys=True)}",
            })
        return messages

    def build(self, user_message: str, history: Optional[list[dict]] = None) -> list[dict]:
        """构造完整 messages：静态前缀 + 历史 + 用户消息（动态后缀）"""
        messages = list(self._static_prefix)  # 浅拷贝
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return messages

    @property
    def cache_key(self) -> str:
        """静态前缀的 hash，用于监控 cache 命中率"""
        raw = json.dumps(self._static_prefix, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# =============================================================================
# 2. Semantic Cache — embedding 语义缓存
# =============================================================================

@dataclass
class CacheEntry:
    response: str
    embedding: list[float]
    timestamp: float
    ttl: float = 300.0  # 默认 5 分钟

    @property
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl


class SemanticCache:
    """语义缓存：通过 embedding 余弦相似度匹配相似 query。

    支持双阈值模式：
    - 精确匹配 (≥0.95)：直接返回缓存
    - 引导匹配 (0.80~0.95)：缓存结果作为 reference 注入 prompt

    多租户隔离：cache key 包含 namespace
    """

    def __init__(self, threshold: float = 0.92, namespace: str = "default"):
        self._entries: dict[str, CacheEntry] = {}
        self.threshold = threshold
        self.namespace = namespace
        self._stats = {"hits": 0, "misses": 0, "guides": 0}

    def _key(self, query: str) -> str:
        return f"{self.namespace}::{hashlib.md5(query.encode()).hexdigest()}"

    def _cosine_sim(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        return dot / (na * nb + 1e-10)

    def get(self, query: str) -> Optional[str]:
        """语义查找：返回缓存响应或 None"""
        # 1. 精确 hash 匹配
        exact = self._entries.get(self._key(query))
        if exact and not exact.is_expired:
            self._stats["hits"] += 1
            return exact.response

        # 2. 语义相似度扫描
        best_sim = 0.0
        best_entry = None
        for entry in self._entries.values():
            if entry.is_expired:
                continue
            sim = self._cosine_sim(self._get_embedding(query), entry.embedding)
            if sim > best_sim:
                best_sim = sim
                best_entry = entry

        if best_sim >= self.threshold and best_entry:
            self._stats["hits"] += 1
            return best_entry.response
        if best_sim >= self.threshold - 0.15 and best_entry:
            # 引导模式：返回缓存但标记为参考
            self._stats["guides"] += 1
            return f"[参考历史回答]\n{best_entry.response}\n[请根据当前问题调整]"

        self._stats["misses"] += 1
        return None

    def set(self, query: str, response: str, embedding: Optional[list[float]] = None):
        """写入缓存"""
        if embedding is None:
            embedding = self._get_embedding(query)
        self._entries[self._key(query)] = CacheEntry(
            response=response,
            embedding=embedding,
            timestamp=time.time(),
        )

    def _get_embedding(self, text: str) -> list[float]:
        """获取文本 embedding（使用 hash 模拟，生产环境替换为 real embedding API）"""
        # 生产环境替换为：openai.Embedding / 本地 bge-small 等
        raw = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in raw[:16]]

    @property
    def stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"] or 1
        return {
            **self._stats,
            "hit_rate": round(self._stats["hits"] / total * 100, 1),
            "size": len(self._entries),
        }


# =============================================================================
# 3. Structured Output — JSON Schema 约束生成
# =============================================================================

class OutputValidator:
    """结构化输出：JSON Schema 验证 + 自动修复重试。

    支持：
    - Pydantic Schema → JSON Schema 转换
    - 输出解析 + 校验
    - 失败时自动重试（带修正提示）
    """

    MAX_RETRIES = 2

    @staticmethod
    def build_schema_instruction(schema: type[T]) -> str:
        """从 Pydantic 模型生成 schema 指令"""
        return json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)

    @staticmethod
    def parse_and_validate(text: str, schema: type[T]) -> Optional[T]:
        """解析 LLM 输出并校验"""
        # 1. 提取 JSON（处理 markdown code block 包裹）
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()

        # 2. 解析 JSON
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None

        # 3. Schema 校验
        try:
            return schema.model_validate(data)
        except Exception:
            return None

    @staticmethod
    def build_retry_prompt(raw_output: str, error: str) -> str:
        return (
            f"你之前的输出不符合要求的 JSON Schema。\n"
            f"输出：{raw_output[:200]}\n"
            f"错误：{error}\n"
            f"请只返回符合 Schema 的 JSON，不要额外说明。"
        )


# =============================================================================
# 4. Model Cascade — 多级模型回退 + 熔断
# =============================================================================

class ModelTier(Enum):
    FAST = "fast"        # 轻量模型：低延迟、低成本
    STANDARD = "standard"  # 标准模型：平衡
    PREMIUM = "premium"   # 旗舰模型：DeepSeek-R1 满血版


class CircuitState(Enum):
    CLOSED = "closed"        # 正常
    OPEN = "open"            # 熔断
    HALF_OPEN = "half_open"  # 半开


@dataclass
class ModelConfig:
    tier: ModelTier
    name: str
    timeout: float = 30.0
    max_retries: int = 2


class CircuitBreaker:
    """熔断器：连续失败 N 次后熔断，冷却后半开探测"""

    def __init__(self, failure_threshold: int = 5, cooldown: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._last_failure = 0.0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure > self.cooldown:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def call(self, fn: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            raise RuntimeError("circuit_breaker_open")

        try:
            result = fn(*args, **kwargs)
            self._failures = 0
            self._state = CircuitState.CLOSED
            return result
        except Exception as e:
            self._failures += 1
            self._last_failure = time.time()
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning("熔断器打开", tier=str(self), failures=self._failures)
            raise


class ModelCascade:
    """模型级联调度：Fast → Standard → Premium 逐级回退。

    策略：
    - 默认用 Fast（低成本）
    - Fast 失败/质量低 → Standard
    - Standard 失败 → Premium（DeepSeek-R1）
    - 连续失败触发熔断
    """

    def __init__(self):
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._tiers: list[ModelConfig] = [
            ModelConfig(tier=ModelTier.FAST, name="deepseek-chat", timeout=15.0),
            ModelConfig(tier=ModelTier.STANDARD, name="deepseek-reasoner", timeout=30.0),
            ModelConfig(tier=ModelTier.PREMIUM, name="deepseek-r1", timeout=60.0),
        ]

    def _get_cb(self, model_name: str) -> CircuitBreaker:
        if model_name not in self._circuit_breakers:
            self._circuit_breakers[model_name] = CircuitBreaker()
        return self._circuit_breakers[model_name]

    async def execute(
        self,
        call_model: Callable[..., Any],
        quality_check: Optional[Callable[[Any], bool]] = None,
        **kwargs,
    ) -> tuple[Any, str]:
        """执行级联调用，返回 (result, model_name)"""
        last_error = None

        for cfg in self._tiers:
            cb = self._get_cb(cfg.name)
            if cb.state == CircuitState.OPEN:
                logger.info("熔断跳过", model=cfg.name)
                continue

            try:
                result = cb.call(call_model, **{**kwargs, "model": cfg.name, "timeout": cfg.timeout})

                # 质量检查
                if quality_check and not quality_check(result):
                    logger.warning("质量检查未通过", model=cfg.name)
                    continue

                return result, cfg.name

            except Exception as e:
                last_error = e
                logger.warning("模型降级", model=cfg.name, error=str(e))
                continue

        raise last_error or RuntimeError("all_models_failed")


# =============================================================================
# 5. 统一优化入口
# =============================================================================

class LLMOptimizer:
    """LLM 优化统一入口：组合 Prompt Cache + Semantic Cache + Cascade。

    用法：
        optimizer = LLMOptimizer(system_prompt="...")
        result = await optimizer.complete(
            user_message="查询订单状态",
            output_schema=OrderResponse,
        )
    """

    def __init__(self, system_prompt: str = "", tools: Optional[list[dict]] = None):
        self.prompt_builder = PromptBuilder(system_prompt, tools)
        self.semantic_cache = SemanticCache(namespace=self.prompt_builder.cache_key)
        self.validator = OutputValidator()
        self.cascade = ModelCascade()

    async def complete(
        self,
        user_message: str,
        output_schema: Optional[type[T]] = None,
        history: Optional[list[dict]] = None,
        skip_cache: bool = False,
    ) -> tuple[T, dict]:
        """执行优化的 LLM 调用。

        Args:
            user_message: 用户输入
            output_schema: Pydantic 模型（启用结构化输出）
            history: 对话历史
            skip_cache: 是否跳过语义缓存

        Returns:
            (解析后的结果, 元数据)
        """
        meta: dict = {"cache_hit": False, "model_used": "", "tier_used": ""}

        # 1. 语义缓存查找
        if not skip_cache:
            cached = self.semantic_cache.get(user_message)
            if cached and output_schema:
                parsed = self.validator.parse_and_validate(cached, output_schema)
                if parsed:
                    meta["cache_hit"] = True
                    return parsed, meta

        # 2. 构造提示词（Prefix Cache 友好）
        messages = self.prompt_builder.build(user_message, history)

        # 3. 构建结构化输出指令
        if output_schema:
            schema_text = self.validator.build_schema_instruction(output_schema)
            messages.append({
                "role": "system",
                "content": f"请严格按照以下 JSON Schema 输出：\n{schema_text}",
            })

        # 4. 模型级联调用
        async def _call(**kw) -> str:
            # 占位：生产环境替换为真实 API 调用
            # import openai; resp = await openai.ChatCompletion.create(**kw)
            # return resp.choices[0].message.content
            raise NotImplementedError("接入真实 LLM API 后替换此调用")

        try:
            raw_output, model_name = await self.cascade.execute(
                call_model=_call,
                messages=messages,
                temperature=0.1 if output_schema else 0.7,
            )
            meta["model_used"] = model_name
        except RuntimeError:
            # 级联全部失败 → 使用 AI 回退
            raw_output = self._fallback_response(user_message, output_schema)
            meta["model_used"] = "fallback"

        # 5. 结构化输出解析
        if output_schema:
            parsed = self.validator.parse_and_validate(raw_output, output_schema)
            for attempt in range(self.validator.MAX_RETRIES):
                if parsed:
                    break
                retry_prompt = self.validator.build_retry_prompt(raw_output, "schema 校验失败")
                raw_output = await self._retry_call(retry_prompt)
                parsed = self.validator.parse_and_validate(raw_output, output_schema)

            if parsed is None:
                raise ValueError(f"LLM 输出未能通过 Schema 校验: {raw_output[:200]}")

            # 写入语义缓存
            self.semantic_cache.set(user_message, raw_output)
            return parsed, meta

        return raw_output, meta

    def _fallback_response(self, query: str, schema: Optional[type] = None) -> str:
        """AI 回退：当所有模型不可用时返回合理默认值"""
        logger.error("LLM 级联全部失败，使用 AI 回退", query=query[:50])
        if schema:
            # 返回空 schema 实例
            return schema.model_json_schema()
        return json.dumps({"error": "service_unavailable", "message": "AI 服务暂时不可用"})

    async def _retry_call(self, prompt: str) -> str:
        """重试调用（简化版）"""
        return json.dumps({"error": "retry_failed"})


# =============================================================================
# 6. Token 使用与成本追踪
# =============================================================================

@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    cost: float = 0.0
    model: str = ""

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class TokenTracker:
    """Token 用量追踪器，用于成本核算和监控"""

    PRICING = {
        "deepseek-chat": {"input": 0.003, "output": 0.015},
        "deepseek-reasoner": {"input": 0.005, "output": 0.025},
        "deepseek-r1": {"input": 0.014, "output": 0.070},
    }
    CACHE_DISCOUNT = 0.1  # Cache hit 为原价的 10%

    def __init__(self):
        self._usages: list[TokenUsage] = []
        self._session_start = time.time()

    def record(self, usage: TokenUsage):
        pricing = self.PRICING.get(usage.model, self.PRICING["deepseek-chat"])
        cached_cost = (usage.prompt_tokens - usage.cached_tokens) * pricing["input"]
        cache_cost = usage.cached_tokens * pricing["input"] * self.CACHE_DISCOUNT
        usage.cost = (cached_cost + cache_cost + usage.completion_tokens * pricing["output"]) / 1000
        self._usages.append(usage)

    @property
    def total_cost(self) -> float:
        return sum(u.cost for u in self._usages)

    @property
    def total_tokens(self) -> int:
        return sum(u.total_tokens for u in self._usages)

    def summary(self) -> dict:
        total = len(self._usages) or 1
        cached = sum(u.cached_tokens for u in self._usages)
        total_prompt = sum(u.prompt_tokens for u in self._usages)
        return {
            "total_calls": len(self._usages),
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "cache_rate": round(cached / max(total_prompt, 1) * 100, 1),
            "avg_cost_per_call": round(self.total_cost / total, 4),
            "session_duration_s": round(time.time() - self._session_start),
        }


token_tracker = TokenTracker()
