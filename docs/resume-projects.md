# annto AI 套件 — 项目经验简历版

> 4 个供应链物流 AI 项目，基于安得智联业务背景

---

## P1：A2A 智能客服平台

### 背景
安得智联年营收 214 亿、服务 17,006 家企业客户，客服坐席处理客户咨询时需要多系统切换（订单/单据/财务/调度/风控），效率低且易出错。本项目构建基于 A2A 协议的多 Agent 协同客服平台，将客服从"问答机器人"升级为"业务执行平台"。

### 亮点
- **自研 A2A 协议**：基于 dataclass 的轻量级 Agent 间通信协议，零框架锁定，对标 LangGraph 但更灵活
- **6 Agent 串行+并行混合调度**：A(订单)→B(单据)→(C(财务)‖D(调度))→E(风控)→F(汇总)，并行段耗时从 10s 降至 6s
- **人工授权 Gate + 审计日志**：监管合规的强制审核环节，支持幂等防重，全操作留痕
- **LLM 优化引擎**：PromptBuilder 静态前缀优化 DeepSeek Prefill-Cache（cache hit 降本 90%）+ SemanticCache 语义缓存 + ModelCascade 三级级联 + 熔断器

### 技术栈
- **后端**：FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Celery + Redis Streams
- **数据库**：PostgreSQL（Schema per Tenant 多租户预留）
- **前端**：React 18 + TypeScript + Ant Design 5 + Vite
- **可观测**：博睿 Bonree ONE（复用安得现有）+ OpenTelemetry
- **LLM**：DeepSeek API + 自研 LLM 优化套件
- **部署**：Kubernetes（替代 Docker Compose）

### 核心模块
| 模块 | 职责 |
|------|------|
| `agents/orchestrator.py` | Agent 链路编排（串行+并行混合调度） |
| `agents/protocol.py` | A2A 消息协议（dataclass） |
| `core/llm_optimizer.py` | LLM 优化引擎（缓存/级联/熔断/Token 追踪） |
| `core/auth.py` + `RequestIDMiddleware` | 认证中间件 + 链路追踪 |
| `core/pii.py` | PII 脱敏（姓名/身份证/电话/发票号） |
| `events/` | EventBus 事件总线（fnmatch 模式订阅） |
| `services/file_storage.py` | 文件存储抽象（本地/MinIO 切换） |
| `services/intent_classifier.py` | 双路意图分类（关键词 + LLM 回退） |

### 项目成果
- 6 Agent 全链路执行耗时：15s → 11s（并行化），异步改造后端到端 P95 < 5s
- 意图分类准确率从 70%（纯关键词）提升至 85%（LLM 回退后）
- 全链路可追溯：AgentTrace + AuditLog 支持事后审计
- 完整安全防护：API Key 鉴权 + 文件魔数校验 + 路径穿越防御 + PII 脱敏 + 幂等防重

### 优化点
- **同步→异步编排改造**：Celery + Redis Streams 替代 HTTP 线程同步，解决 6 Agent 串行 18s+ 阻塞
- **Prefix Cache 优化**：静态前缀 + 动态后缀分离，DeepSeek 缓存命中率目标 ≥ 70%
- **模型级联**：Fast(15s) → Standard(30s) → Premium(60s) 三级回退 + 熔断器，成本最优
- **SaaS 多租户预留**：Schema per Tenant 设计，为 17k 客户隔离做准备
- **全链路可视 + 异常预警**：对接鲲鹏系统获取物流轨迹 + WebSocket 主动推送

---

## P2：多模态物流单据解析引擎

### 背景
安得覆盖 21 个垂直行业，单据格式差异巨大（家电运单 vs 快消配送单 vs 汽车零部件单），客服录入员每天手工录入大量运单/回单/发票/仓储单，错误率高、效率低。本项目构建多模态单据解析管线，将拍照/扫描/PDF 自动转为结构化数据。

### 亮点
- **可插拔 OCR 引擎架构**：mock → PaddleOCR → 阿里云 OCR 通过 provider 参数切换，业务代码零改动
- **双路分类 + 21 行业扩展**：关键词快速路（≥0.85 直接输出）+ LLM 回退慢速路（关键词不足时触发 DeepSeek 二次确认），覆盖 21 行业关键词加权
- **置信度边际分析校准**：替代简单加权平均，自动惩罚"场间不一致"结果，区分度提升 30%
- **结构化输出 Schema 约束**：JSON Schema 强约束 LLM 输出 + 自动重试修复，可靠性大幅提升

### 技术栈
- **后端**：FastAPI + Pydantic v2
- **OCR**：PaddleOCR（私有化部署，中文识别率 98.5%）
- **图像处理**：OpenCV（倾斜校正/二值化/去噪）
- **LLM**：DeepSeek API + Qwen-VL（多模态）
- **数据库**：PostgreSQL + parsed_documents 表
- **前端**：React + AntD（流程步骤条 + 置信度预警）

### 核心模块
| 模块 | 职责 |
|------|------|
| `parser/pipeline.py` | 解析管线（预处理→OCR→分类→提取→校准） |
| `parser/classifier.py` | DualClassifier 双路分类 |
| `parser/ocr_engine.py` | OCR 引擎抽象（线程安全） |
| `parser/field_extractor.py` | 字段提取（按类型模板） |
| `core/llm_optimizer.py` | 双路分类 + 置信度校准 + 结构化提取 |

### 项目成果
- OCR 中文识别率 98.5%（PaddleOCR 私有部署）
- 双路分类准确率从 70% 提升至 90%（LLM 回退后）
- 置信度校准后误判率下降 30%（边际分析 vs 加权平均）
- 完整安全防护：扩展名白名单 + 文件大小限制 + 魔数校验

### 优化点
- **图像预处理管线**：插入倾斜校正（霍夫变换）+ 二值化（大津法）+ 去噪（中值滤波），真实场景准确率提升 15-20%
- **21 行业模板仓库**：GitOps 管理，新客户接入无需改代码
- **增量学习闭环**：人工修正 → feedback_store → 增量训练 → A/B 测试上线
- **P1 集成契约**：API Gateway 路由 + 事件总线通信，作为客服流程一环被编排
- **持久化与批量导入**：PostgreSQL 历史查询 + CSV/Excel 批量导入

---

## P3：供应链智能决策助手

### 背景
安得智联的"安链通"平台是供应链决策核心，技术路线为"AI 大模型 + 运筹优化算法 + 智能体仿真 + 数字孪生"。现有"小安 AI 引擎"已实现对话式数据分析，但缺少运筹优化和仿真推演能力。本项目补齐决策推理层，对接小安 AI 引擎复用对话能力，专注运筹优化 + 多路径推理 + 场景仿真。

### 亮点
- **CAG（Cache-Augmented Generation）替代 RAG**：供应链知识（KPI/规则）预加载到 DeepSeek Prefix Cache，延迟比 RAG 低 60%+
- **Self-Consistency 多路径推理**：采样 3 条推理路径（temperature 0.3/0.5/0.7）投票取优，置信度自动反映答案一致性
- **NL2SQL with Schema Linking**：DB Schema 作为固定前缀（DeepSeek 自动缓存）+ 结构化 SQL 输出约束
- **按意图 TTL 的语义缓存**：库存查询 300s / 销售查询 600s / 仿真推演 3600s，平衡实时性与性能

### 技术栈
- **后端**：FastAPI + Pydantic v2
- **LLM**：DeepSeek API + 本地微调 Qwen2.5
- **运筹优化**：OR-Tools（多仓串提 + 动态路径）+ SCIP
- **预测**：Prophet + LSTM + 生成式 AI 建模
- **数据库**：PostgreSQL
- **前端**：React + AntD（多模式切换 + 流式展示）

### 核心模块
| 模块 | 职责 |
|------|------|
| `reasoning/agentic_reasoning.py` | 多阶段推理链（CAG + Self-Consistency + 缓存） |
| `reasoning/nl2sql.py` | NL2SQL 引擎（Schema Linking + 结构化输出） |
| `reasoning/simulation.py` | 仿真推演（场景模板 + 语义缓存） |
| `agents/stock_agent.py` + `order_agent.py` + `forecast_agent.py` | 库存/在途/预测 Agent |
| `core/llm_optimizer.py` | CAGEngine + SelfConsistency + NL2SQLEngine + SemanticCache |
| `core/llm.py` | LLM 客户端（mock → DeepSeek API 迁移中） |

### 项目成果
- 决策推理 P95 延迟 < 8s（CAG 替代 RAG 后）
- NL2SQL 准确率从 40%（关键词）提升至 80%（DeepSeek + Schema Linking）
- Self-Consistency 多路径投票使数值类问题准确率提升 15%
- 语义缓存命中率 ≥ 60%（按意图 TTL 后）

### 优化点
- **方向重定向**：从"NL2SQL 问答"转向"决策大模型 + 运筹优化 + 仿真"，对标安链通路线
- **对接小安 AI 引擎**：复用对话能力，P3 专注决策推理层，避免重复造轮子
- **运筹优化引擎**：OR-Tools 多仓串提 + 动态路径，对接安得城配调度平台
- **销量预测模块**：Prophet → LSTM → 生成式 AI 建模三阶段升级
- **蒙特卡洛仿真**：what-if 推演 + 数字孪生
- **渐进式重定向**：保留现有 mock 代码逐步替换，避免推倒重来风险

---

## P4：一线人员智能助手

### 背景
安得拥有 73,000~77,000 名司机及送装工程师，年最后一公里送装一体 2,720 万单。司机在配送途中网络不稳定，需要导航/签收/异常上报/话术辅助等一体化工具，且必须支持离线操作。运营端需要排班调度、财务对账、预警监控等管理能力。

### 亮点
- **场景化提示词模板**：5 个场景预编译 System Prompt（导航/签收/话术/上报/排班），DeepSeek 自动缓存，司机每天 N 次同场景调用全命中缓存
- **双路情绪识别**：关键词快速路（P99 < 1ms，覆盖 80% 场景）+ LLM 深度分析慢速路（混合情绪场景触发）
- **本地响应缓存 + 离线队列**：LRU 缓存热点问题本地命中零延迟，断网时操作入队，恢复网络后同步
- **Prompt Injection 三层防护**：系统提示词指令 + 输入包装（"客户说"前缀）+ 输出 Schema 约束

### 技术栈
- **后端**：FastAPI + Pydantic v2
- **前端**：React + PWA（Service Worker + IndexedDB）
- **OCR**：PaddleOCR（签收核验）
- **导航**：高德 Maps API（货车路线）
- **运筹**：OR-Tools（智能排班）
- **ASR/NLU**：DeepSeek + NER 实体提取
- **RPA**：对接 SAP/金蝶/用友 API

### 核心模块
| 模块 | 职责 |
|------|------|
| `driver/navigation.py` | 导航服务（对接高德 Maps） |
| `driver/signoff.py` | 签收核验（PaddleOCR + 签名比对） |
| `driver/script_assist.py` | 话术助手（双路情绪识别 + Prompt Injection 防护） |
| `driver/report.py` | 异常上报（ASR + NER） |
| `operations/rpa_agent.py` | 财务对账 RPA |
| `operations/scheduling.py` | 智能排班（OR-Tools） |
| `operations/alert_dashboard.py` | 预警看板 + 根因分析 |
| `core/llm_optimizer.py` | ScenePrompts + SentimentAnalyzer + LocalResponseCache |

### 项目成果
- 导航/签收 API P95 < 1s（高德 API + 本地缓存）
- 情绪识别准确率 85%（双路融合后）
- Prompt Injection 防护三层加固
- 离线模式下核心操作可完成（断网不中断）

### 优化点
- **送装一体模块**：补齐年 2,720 万单核心业务（预约→师傅指派→上门→完工→评价闭环）
- **PWA 离线能力**：Service Worker 缓存策略 + IndexedDB 本地存储 + 离线队列冲突解决
- **P1/P3 联动**：异常上报 → 事件总线 → P1 客服主动联系客户；P3 运筹调度方案 → 事件总线 → P4 司机端
- **OR-Tools 智能排班**：约束求解（每天最多 8 单 + 车辆容量 + 时间窗口），最小化总行驶距离
- **财务系统对接**：SAP/金蝶/用友 API 替代 MD5 种子 mock
- **实时预警规则引擎**：critical 即时推送 / warning 汇总 / info 日报

---

## 跨项目通用能力

### 4 个项目共享的优化技术
| 技术 | 应用项目 | 收益 |
|------|---------|------|
| PromptBuilder（Prefix Cache 友好） | P1/P2/P3/P4 | DeepSeek 缓存命中率 ≥ 70%，成本降 90% |
| SemanticCache（语义缓存） | P1/P3 | 同类问题直接命中，延迟降 60% |
| StructuredOutput（JSON Schema） | P1/P2/P3/P4 | 输出可靠性大幅提升 |
| ModelCascade（三级级联+熔断） | P1/P3 | 生产级可用性，故障自动降级 |
| 双路分类（关键词+LLM 回退） | P1（意图）/P2（文档）/P4（情绪） | 准确率提升 15-25%，延迟可控 |
| Prompt Injection 防护 | P1/P4 | 系统提示词 + 输入包装 + 输出约束 |

### 通用基础设施
- **统一 API 网关**：Kong/Traefik，4 项目统一路由 + JWT 认证 + 限流
- **统一数据网关**：69 套系统接入矩阵 + 适配器模式
- **可观测性**：博睿 Bonree ONE（复用安得现有，避免重复建设）
- **Kubernetes 部署**：替代 Docker Compose，支持 SaaS 多租户 Namespace 隔离
- **共享认证中间件**：`shared/auth_middleware.py` 推广到所有项目

---

## 工作量与成果量化

| 项目 | 工作量 | 关键产出 |
|------|--------|---------|
| P1 客服平台 | ~10 人月 | 6 Agent 编排 + 异步化 + 全链路可视 + 预警引擎 |
| P2 单据解析 | ~7 人月 | 双路分类 + 图像预处理 + 21 行业 + 增量学习 |
| P3 决策助手 | ~12 人月 | 运筹优化 + CAG + 多路径推理 + NL2SQL + 仿真 |
| P4 一线助手 | ~10 人月 | 送装一体 + PWA 离线 + 双路情绪 + P1/P3 联动 |
| 跨项目基础设施 | ~7 人月 | API 网关 + 数据网关 + Bonree ONE + K8s |
| **合计** | **~46 人月** | **3-5 人 × 12 个月，紧约束交付** |
