# The World — 剩余工作 TODO

> 已完成: Phase 0 (项目骨架) + Phase 1 (角色系统) + Phase 2 (模拟引擎核心) + Phase 3 (AI集成) + Phase 4 (关系与社交)
> 当前测试: 后端 152/152 通过, 前端 TypeScript 零错误
> 更新日期: 2026-03-04

---

## P0 稳定性冲刺 (进行中)

- [x] 盘点前后端核心 API 契约（auth/characters/worlds/simulation/relationships/ws）
- [x] 修复高风险契约偏差：角色更新接口支持 `PUT/PATCH` 双方法兼容
- [x] 补充后端回归测试：`PATCH /api/v1/characters/{id}`
- [x] 扩展前端 store/API 层契约测试覆盖
- [x] 最小链路联调验收（登录→创建角色→更新→进入世界→模拟控制）
- [x] 输出 API 契约基线文档（docs/api_contract.md）
- [x] 增加 OpenAPI 契约守卫测试（关键路径/方法不漂移）

---

## ~~Phase 3: AI 集成 (三层路由)~~ ✅ 已完成

- [x] AI Router 三层路由决策 (重要度分类 + 预算 + 降级)
- [x] Tier 3: 规则 FSM (模板响应 + 人格变体)
- [x] Tier 2: Ollama 本地 LLM (httpx + trust_env=False)
- [x] Tier 1: Claude API (Anthropic SDK + 每用户预算)
- [x] 人格模型 (Big Five → 行为修正 + prompt)
- [x] 对话 UI (Phaser 气泡 + React ChatLog + WS)
- [x] 记忆系统 (MemoryManager: 创建/检索/重要度+时效+情感权重)

---

## ~~Phase 4: 关系与社交~~ ✅ 已完成

- [x] RelationshipService 核心服务层 (get_or_create, evolve, compatibility, classify)
- [x] REST API (GET /relationships/{id}, GET /relationships/{id}/{target_id})
- [x] AI 集成接入 (真实关系分数 + evolve + milestone 事件 + interaction_summary)
- [x] 社交活动增强 (DEEP_TALK + GROUP_HANGOUT + nearby_characters 加成)
- [x] 前端关系面板 (RelationshipPanel + Zustand store + WS 更新)
- [x] 交互历史摘要 (interaction_summary JSONB, 最多 20 条)

---

## Phase 5: 社区功能

### 5.1 公开 OC 画廊
- [ ] 搜索/筛选功能增强
- [ ] 角色详情页

### 5.2 跨用户角色互动
- [ ] 将 OC 放入他人世界
- [ ] 权限和隐私控制

### 5.3 故事分享
- [ ] 故事/事件日志导出和分享
- [ ] 精彩片段保存

### 5.4 Toyhouse 导入
- [ ] JSON 格式映射
- [ ] 导入 UI 流程

### 5.5 随机事件 + 季节事件
- [ ] 随机事件系统 (捡到猫/下雨天/意外访客)
- [ ] 季节节日、角色生日

### 5.6 UI 打磨
- [ ] 响应式布局优化
- [ ] 无障碍 (a11y)
- [ ] 动画和过渡效果

### 5.7 验证
- [ ] 社区可分享角色、互访世界、导入现有 OC

---

## Phase 6: 进阶功能 (持续)

- [ ] 向量检索记忆 (embedding 相似度)
- [ ] 人格随时间演化
- [ ] 插件/Mod 系统
- [ ] 高级世界编辑器
- [ ] 移动端适配
- [ ] i18n 国际化

---

## 基础设施待办

- [ ] Docker Compose 全栈测试 (用户尚未安装 Docker)
- [ ] GitHub Actions CI (ruff + eslint + mypy + tsc + pytest + vitest)
- [ ] Alembic 数据库迁移 (目前用 SQLite auto-create)
- [ ] PostgreSQL 生产环境配置
- [ ] Redis 缓存集成
- [ ] 前端代码分割 (当前 bundle 1.7MB)

---

## 当前架构参考

```
后端 152 测试:
  - 23 API 测试 (auth + characters + health + relationships)
  - 23 关系服务测试 (compatibility + classify + get_or_create + evolve + summary)
  - 74 AI 测试 (integration + memory + personality + router + tier1/2/3)
  - 32 模拟引擎测试 (clock + needs + autonomy + engine)

模拟引擎组件:
  - clock.py      — 游戏时钟 (tick/hour/day/season)
  - needs.py      — 六大需求 (hunger/energy/social/fun/hygiene/comfort)
  - activities.py — 21 个核心活动 (含 deep_talk + group_hangout)
  - autonomy.py   — Utility-based 决策 (紧迫度50% + 人格30% + 随机20% + 社交加成)
  - engine.py     — SimPy + asyncio 核心循环 (nearby_characters 传递)
  - world_seed.py — Starter Town (6 地点)

AI 三层架构:
  - router.py     — 交互分类 + 层级路由 + 降级
  - tier1_claude  — Claude API (10%, 关键场景)
  - tier2_ollama  — Ollama 本地 LLM (80%, 日常对话)
  - tier3_rules   — 规则 FSM (10%, 基础反应)
  - personality   — Big Five → prompt 指令
  - memory        — 记忆管理 (创建/检索/重要度排序)
  - integration   — 引擎桥接 (encounter → dialogue → memory → relationship)

关系系统:
  - relationship_service — 关系 CRUD + 兼容性 + 进化 + 里程碑
  - API: GET /relationships/{id}, GET /relationships/{id}/{target_id}

API 端点:
  - POST /api/v1/simulation/{world_id}/start
  - POST /api/v1/simulation/{world_id}/pause
  - POST /api/v1/simulation/{world_id}/speed
  - GET  /api/v1/simulation/{world_id}/state
  - GET  /api/v1/relationships/{character_id}
  - GET  /api/v1/relationships/{character_id}/{target_id}
  - WS   /api/v1/ws/{world_id}
```
