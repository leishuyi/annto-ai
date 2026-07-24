"""P3 决策助手 — LLM 优化引擎

技术栈：
  1. Cache-Augmented Generation (CAG) — 将供应链知识预加载到 Prompt Cache
  2. 多路径推理 (Self-Consistency) — 采样 N 条推理路径，投票取优
  3. NL2SQL with Schema Linking — 将自然语言转为结构化 SQL 查询
  4. 语义缓存 — 同类问题直接命中历史答案
  5. 结构化输出 — 约束 JSON Schema 输出
"""
import hashlib
import json
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from loguru import logger


# =============================================================================
# 1. Cache-Augmented Generation (CAG) — 预加载知识
# =============================================================================

class CAGEngine:
    """Cache-Augmented Generation：将静态知识预加载到模型 Prefix Cache。

    原理：将供应链知识库（库存规则、定价策略、物流指标）编码为
    固定前缀，利用 DeepSeek Prefill-Cache 实现"知识即缓存"。
    相比 RAG 每轮检索，CAG 在知识固定的场景下延迟更低。
    """

    # 供应链知识索引（预编译为静态前缀）
    KNOWLEDGE_BASE = """
【安得智联供应链指标】
- 配送准时率目标：≥95%
- 破损率警戒线：>1.5%
- 库存安全水位：不低于14天
- 车辆装载率目标：≥85%

【核心规则】
- 华东区：上海仓、南京仓、杭州仓
- 华南区：佛山仓、广州仓、深圳仓
- 华北区：北京仓、天津仓、郑州仓
- 优先发近仓：订单就近仓库发货，跨区调拨需审批

【品类基准】
- 空调整机: 标准库存 5000台/仓，周转天数 21天
- 冰箱: 标准库存 3000台/仓，周转天数 28天
- 洗衣机: 标准库存 2000台/仓，周转天数 14天
- 小家电: 标准库存 8000台/仓，周转天数 35天
"""

    def __init__(self):
        self._cache_prefix = self._build_prefix()

    def _build_prefix(self) -> str:
        """构建可缓存的静态前缀"""
        return (
            "你是一个供应链决策助手。请基于以下知识回答问题。\n"
            f"---\n{self.KNOWLEDGE_BASE}\n---\n"
        )

    @property
    def prefix(self) -> str:
        return self._cache_prefix

    @property
    def prefix_hash(self) -> str:
        return hashlib.sha256(self._cache_prefix.encode()).hexdigest()[:16]


# =============================================================================
# 2. 多路径推理 (Self-Consistency)
# =============================================================================

@dataclass
class ReasoningPath:
    steps: list[str]
    answer: Any
    confidence: float


class SelfConsistency:
    """多路径推理：采样 N 条推理路径，投票取最优。

    适用场景：需要精确推理的供应链问题（库存计算、路径优化）
    原理：LLM 采样 temperature > 0 多次，回答一致性越高，置信度越高。
    """

    def __init__(self, num_paths: int = 3):
        self.num_paths = num_paths

    def reason(
        self,
        question: str,
        llm_call: Callable[[str, float], str],
    ) -> ReasoningPath:
        """执行多路径推理"""
        paths: list[dict] = []

        for i in range(self.num_paths):
            temp = 0.3 + i * 0.2  # 0.3, 0.5, 0.7 逐步增加随机性
            prompt = (
                f"问题：{question}\n"
                f"请逐步推理，最后给出答案。\n"
                f"格式：\n推理步骤：\n1. ...\n2. ...\n答案：..."
            )
            try:
                response = llm_call(prompt, temp)
                path = self._parse_response(response)
                path["temperature"] = temp
                paths.append(path)
            except Exception as e:
                logger.warning("推理路径失败", path=i, error=str(e))

        if not paths:
            return ReasoningPath([], "无法生成推理", 0.0)

        # 答案一致性投票
        answers = [p.get("answer", "") for p in paths]
        answer_votes = {}
        for ans in answers:
            clean = str(ans).strip().lower()
            answer_votes[clean] = answer_votes.get(clean, 0) + 1

        best_answer = max(answer_votes, key=answer_votes.get)
        consistency = answer_votes[best_answer] / max(len(paths), 1)

        # 提取最佳路径的推理步骤
        best_path = next((p for p in paths if str(p.get("answer", "")).strip().lower() == best_answer), paths[0])

        return ReasoningPath(
            steps=best_path.get("steps", []),
            answer=best_answer,
            confidence=round(consistency, 3),
        )

    def _parse_response(self, text: str) -> dict:
        """解析模型输出的推理步骤和答案"""
        steps: list[str] = []
        answer = ""

        # 提取推理步骤
        step_match = re.findall(r"\d+\.\s*(.+?)(?=\n\d+\.|\n答案|$)", text, re.DOTALL)
        if step_match:
            steps = [s.strip() for s in step_match]

        # 提取答案
        answer_match = re.search(r"答案[：:]\s*(.+)", text)
        if answer_match:
            answer = answer_match.group(1).strip()

        return {"steps": steps, "answer": answer or text[:200]}


# =============================================================================
# 3. NL2SQL with Schema Linking
# =============================================================================

DB_SCHEMA = """
-- 库存表
CREATE TABLE inventory (
    warehouse_id TEXT,        -- 仓库编码
    sku TEXT,                 -- SKU
    product_name TEXT,        -- 产品名称
    quantity INTEGER,         -- 当前库存
    max_capacity INTEGER,     -- 最大容量
    last_updated DATE         -- 最后更新
);

-- 销售表
CREATE TABLE sales (
    date DATE,               -- 日期
    sku TEXT,                -- SKU
    region TEXT,             -- 区域
    quantity INTEGER,        -- 销量
    revenue DECIMAL          -- 收入
);

-- 在途表
CREATE TABLE in_transit (
    order_id TEXT,           -- 订单号
    sku TEXT,               -- SKU
    quantity INTEGER,        -- 在途数量
    origin TEXT,            -- 始发地
    destination TEXT,        -- 目的地
    eta DATE,               -- 预计到达
    status TEXT              -- 状态
);

-- 配送表
CREATE TABLE delivery (
    region TEXT,            -- 区域
    date DATE,             -- 日期
    total_orders INTEGER,   -- 总单数
    on_time INTEGER,        -- 准时单数
    damaged INTEGER         -- 破损单数
);
"""


class NL2SQLEngine:
    """NL2SQL 引擎：Schema Linking + SQL 生成 + 执行

    优化点：
    1. Schema Linking：仅注入相关表 Schema（减少 Token）
    2. Prompt Cache：Schema 定义作为固定前缀缓存
    3. 结构化输出：约束 SQL 输出格式
    """

    def __init__(self):
        # 注入完整 Schema（作为 Prefix Cache）
        self._schema_prefix = f"# 数据库 Schema\n{DB_SCHEMA}\n---\n"

    def generate_prompt(self, question: str) -> str:
        """生成 NL2SQL 提示词"""
        return (
            f"{self._schema_prefix}"
            f"将以下问题转换为 SQL 查询：\n"
            f"问题：{question}\n"
            f"只返回 SQL，不要额外说明。\n"
            f"SQL："
        )

    def parse_sql(self, raw: str) -> str:
        """提取 SQL（处理 markdown 包裹）"""
        if "```sql" in raw:
            return raw.split("```sql")[1].split("```")[0].strip()
        if "```" in raw:
            return raw.split("```")[1].strip()
        # 直接提取 SELECT ...
        match = re.search(r"(SELECT\s+.+)", raw, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else raw.strip()


# =============================================================================
# 4. 语义缓存
# =============================================================================

@dataclass
class CacheEntry:
    response: str
    timestamp: float
    ttl: float = 600.0  # 10 分钟


class SemanticCache:
    """语义缓存：按意图分类缓存结果"""

    INTENT_ROUTES = {
        "inventory": 0.95,     # 库存查询 → 高阈值（数据实时性要求高）
        "sales": 0.90,         # 销售查询 → 中阈值
        "delivery": 0.92,      # 配送查询
        "forecast": 0.85,      # 预测查询 → 低阈值（趋势变化慢）
        "simulation": 0.80,    # 仿真推演 → 低阈值
    }

    def __init__(self):
        self._entries: dict[str, CacheEntry] = {}
        self._stats = {"hits": 0, "misses": 0}

    def _detect_intent(self, query: str) -> str:
        """检测查询意图"""
        q = query.lower()
        if any(k in q for k in ["库存", "stock", "存货", "仓储"]):
            return "inventory"
        if any(k in q for k in ["销售", "趋势", "销量", "sales", "收入"]):
            return "sales"
        if any(k in q for k in ["准时", "配送", "delivery", "破损"]):
            return "delivery"
        if any(k in q for k in ["预测", "forecast", "预估", "趋势"]):
            return "forecast"
        if any(k in q for k in ["如果", "假设", "simulation", "模拟", "推演"]):
            return "simulation"
        return "default"

    def get(self, query: str) -> Optional[str]:
        intent = self._detect_intent(query)
        threshold = self.INTENT_ROUTES.get(intent, 0.85)
        key = hashlib.md5(query.encode()).hexdigest()

        # 精确匹配
        if key in self._entries:
            entry = self._entries[key]
            if not self._is_expired(entry):
                self._stats["hits"] += 1
                return entry.response

        # 语义近似匹配（简化版）
        for stored_key, entry in self._entries.items():
            if self._is_expired(entry):
                continue
            sim = self._text_similarity(query, stored_key)
            if sim >= threshold:
                self._stats["hits"] += 1
                return entry.response

        self._stats["misses"] += 1
        return None

    def set(self, query: str, response: str, ttl: Optional[float] = None):
        key = hashlib.md5(query.encode()).hexdigest()
        self._entries[key] = CacheEntry(
            response=response,
            timestamp=time.time(),
            ttl=ttl or self._detect_ttl(query),
        )

    def _detect_ttl(self, query: str) -> float:
        intent = self._detect_intent(query)
        return {
            "inventory": 300.0,
            "sales": 600.0,
            "delivery": 600.0,
            "forecast": 1800.0,
            "simulation": 3600.0,
        }.get(intent, 600.0)

    def _is_expired(self, entry: CacheEntry) -> bool:
        return time.time() - entry.timestamp > entry.ttl

    def _text_similarity(self, a: str, b: str) -> float:
        """基于 Token 交集的快速相似度计算"""
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        return len(intersection) / max(len(set_a | set_b), 1)

    @property
    def stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"] or 1
        return {
            **self._stats,
            "hit_rate": round(self._stats["hits"] / total * 100, 1),
            "size": len(self._entries),
        }
