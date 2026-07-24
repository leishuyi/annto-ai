# annto AI 套件 — 代码级查缺补漏报告

> 审查日期：2026-07-24 | 基于完整源码审查

## 已修复问题

| # | 问题 | 项目 | 文件 | 严重性 |
|---|------|------|------|--------|
| ✅ | `datetime.now(timezone.utc)()` 语法错误导致运行时崩溃 | P1 | `orchestrator.py:62` | 🔴 阻塞 |
| ✅ | `allow_origins=["*"]` + `allow_credentials=True` 冲突（FastAPI 启动警告） | P2/P3/P4 | `main.py` | 🟠 严重 |
| ✅ | upload_dir 使用相对路径，工作目录变化时文件丢失 | P1 | `config.py` | 🟠 严重 |
| ✅ | API Key 空字符串时跳过所有鉴权，开发/生产配置混淆 | P1 | `config.py` | 🔴 致命 |
| ✅ | 数据库连接池无限制，100 并发即耗尽连接 | P1 | `session.py` | 🟠 严重 |
| ✅ | 全局异常无 request_id，无法链路追踪 | P1 | `main.py` | 🟠 严重 |
| ✅ | P2/P3/P4 完全无 API 认证中间件 | P2/P3/P4 | 新增 `core/auth.py` | 🔴 致命 |

## 一、P1 客服平台 — 剩余未修复漏洞

### 1.1 安全漏洞

| # | 问题 | 文件 | 说明 | 建议 |
|---|------|------|------|------|
| S1 | 文件上传无并发限制 | `routers/documents.py:88` | 大量并发上传可耗尽内存/磁盘 | 添加 UploadRateLimiter |
| S2 | PII 脱敏未在 API 层实施 | `schemas/agent.py:14-15` | AgentTrace 直接暴露 input_data/output_data 可能含身份证/电话 | 在 response_model 层调用 pii.mask_* |
| S3 | CORS 配置硬编码 origins | `config.py:32` | 多环境需不同 origins | 通过环境变量注入 |
| S4 | API Key 校验使用字符串对比 | `core/auth.py:30` | 时序攻击风险 | 使用 `hmac.compare_digest` |

### 1.2 架构缺陷

| # | 问题 | 文件 | 说明 | 建议 |
|---|------|------|------|------|
| A1 | Agent 链路仍为同步执行 | `agents/orchestrator.py:47` | HTTP 线程阻塞 18s+ | 改为 Celery 异步任务 |
| A2 | 无状态轮询端点 | 缺失 | `POST /run` 同步等待完成后才返回 | 增加 `GET /{id}/status` 返回 202 |
| A3 | 事件总线纯同步阻塞 | `events/__init__.py` | 订阅者异常会阻塞发布者 | 改为异步 Queue |
| A4 | Agent 并行功能未启用 | `config.py:16` | `feature_agent_parallel=False` | 启用并行并测试 |
| A5 | Agent 失败后只能全量重跑 | `orchestrator.py:84` | 无断点续跑功能 | 支持从失败 Agent 重试 |

### 1.3 功能缺失

| # | 问题 | 说明 | 建议 |
|---|------|------|------|
| M1 | 无物流轨迹追踪 | 业务核心需求"全链路可视" | 新增 Tracking Agent + API |
| M2 | 无异常预警推送 | 业务需求"自动监测+主动推送" | 新增 AlertEngine + WebSocket |
| M3 | 无 SaaS 多租户 | 安得服务 17,006 家客户 | Schema per Tenant |
| M4 | 无 69 系统对接规划 | 所有 Agent 需要真实数据 | 统一数据网关 |

### 1.4 代码质量

| # | 问题 | 文件 | 说明 |
|---|------|------|------|
| Q1 | Agent 全部返回硬编码 mock | 6 个 agent 文件 | 无真实 LLM/数据源调用 |
| Q2 | `main.py:25` create_all 影响性能 | `main.py` | 生产环境不应 auto-migrate |
| Q3 | 无请求速率限制 | - | 生产需防刷 |

## 二、P2 单据解析 — 剩余未修复漏洞

### 2.1 安全漏洞

| # | 问题 | 文件 | 建议 |
|---|------|------|------|
| S1 | 上传文件无魔数校验 | `main.py:40` | 参考 P1 documents.py 的 `_verify_magic_bytes` |
| S2 | 解析后删除原文件不可重试 | `main.py:50-51` | 保留源文件，增加重试机制 |
| S3 | 无数据库连接配置 | - | 需增加 PostgreSQL 配置 |

### 2.2 架构缺陷

| # | 问题 | 说明 | 建议 |
|---|------|------|------|
| A1 | 无持久化 | 解析结果不保存 | 新增 PostgreSQL + parsed_documents 表 |
| A2 | 无图像预处理 | 真实场景需倾斜校正/去噪/二值化 | 新增 ImagePreprocessor |
| A3 | 置信度仅简单加权 | `pipeline.py:22` | 引入边际分析校准 |
| A4 | 分类仅 5 类（业务需 21 行业）| `schemas/document.py:7` | 扩展行业分类体系 |
| A5 | 与 P1 无集成 | - | 定义 API 契约 |

## 三、P3 决策助手 — 剩余未修复漏洞

### 3.1 安全漏洞

| # | 问题 | 文件 | 建议 |
|---|------|------|------|
| S1 | LLM 静默回退 mock 无告警 | `core/llm.py:18` | 失败时应有监控告警 |
| S2 | 无输入长度限制 | `main.py:27` | 长文本可耗尽 Token |

### 3.2 架构缺陷（严重）

| # | 问题 | 说明 | 建议 |
|---|------|------|------|
| A1 | **方向性错误** | 定位 NL2SQL 问答，业务需决策大模型+运筹优化 | 全面重定向 |
| A2 | 全部 mock | 4 个 if-else 关键词匹配 | 逐个替换真实实现 |
| A3 | 无运筹优化 | 业务核心"多仓串提+动态路径" | 引入 OR-Tools |
| A4 | 无数据库 | 重启数据丢失 | 新增 PostgreSQL |

## 四、P4 一线助手 — 剩余未修复漏洞

### 4.1 安全漏洞

| # | 问题 | 文件 | 建议 |
|---|------|------|------|
| S1 | 导航 API 无输入校验 | `main.py:27` | 起目的地参数校验 |
| S2 | 签收永远成功 | `driver/signoff.py:5` | 制造虚假安全感 |

### 4.2 架构缺陷

| # | 问题 | 说明 | 建议 |
|---|------|------|------|
| A1 | 送装一体模块缺失 | 年 2,720 万单核心业务 | 新增 InstallationService |
| A2 | 无离线能力 | 73k 司机网络不稳定 | PWA + IndexedDB |
| A3 | 无 P1/P3 协同 | 预警/调度各自独立 | 事件总线联动 |
| A4 | prompt injection 防护无真实验证 | `driver/script_assist.py` | llm.chat 是 mock，防护未生效 |

## 五、跨项目缺陷

| # | 问题 | 严重性 | 说明 |
|---|------|--------|------|
| X1 | 无统一 API 网关 | 🔴 致命 | 4 个独立端口，无统一路由/限流/认证 |
| X2 | shared/auth_middleware.py 未被引用 | 🟠 严重 | 共享中间件在各项目根目录但无人引用 |
| X3 | 无 network 统一管理 | 🟠 严重 | 4 个 docker-compose 各自独立网络 |
| X4 | 健康检查全部 return {"status": "ok"} | 🟠 严重 | 未检查 DB/Redis/LLM 可达性 |
| X5 | 无 .env.example 文件 | 🟠 中 | 新开发者无法快速配置 |
| X6 | 缺少 requirements.txt/pyproject.toml | 🟠 中 | 无法直接 pip install |
| X7 | 4 个项目前端 package.json 版本不同步 | 🟢 低 | antd/vite 版本不一致 |

## 修复优先级建议

| 优先级 | 问题 | 建议工时 |
|--------|------|---------|
| **P0** | P3 全面重定向（方向性错误）| 4 周 |
| **P0** | P1 异步编排改造 | 1 周 |
| **P0** | P1 全链路可视 + 异常预警 | 3 周 |
| **P0** | P4 送装一体模块 | 6 周 |
| **P1** | P2 与 P1 集成 + 持久化 | 2 周 |
| **P1** | 统一 API 网关 | 3 周 |
| **P1** | P4 离线能力 | 4 周 |
| **P2** | 可观测性（博睿 ONE 集成）| 2 周 |
| **P2** | 69 系统对接规范 | 4 周 |
| **P3** | 其余代码质量修复 | 持续 |
