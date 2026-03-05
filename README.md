<div align="center">

# The World (世界)

**开源OC生活模拟平台 - 让你的原创角色活起来**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)](CONTRIBUTING.md)

<img src="docs/assets/banner.png" alt="The World Banner" width="600" />

*创建你的OC，赋予ta独特的个性，然后看ta在一个活生生的世界中自主生活。*

[快速开始](#快速开始-quick-start) · [功能特性](#特性-features) · [技术栈](#技术栈-tech-stack) · [路线图](#开发路线图-roadmap) · [参与贡献](#贡献指南-contributing)

</div>

---

## 简介 (Introduction)

**The World（世界）** 是一个开源的、基于Web的类Sims生活模拟平台，专为**原创角色（OC）** 设计。

你可以在这里为你的OC创建详细的人格档案、外貌设定和背景故事，然后将ta放入一个由AI驱动的模拟世界中。角色会基于自身的性格特征自主做出决策——吃饭、社交、工作、恋爱——你可以观察ta的生活，也可以随时介入引导。

### 核心亮点

- **深度角色创建**：基于Big Five人格模型的性格系统，让每个角色都独一无二
- **AI驱动行为**：三层混合AI架构（Claude API + 本地Ollama + 规则引擎），让角色行为既智能又经济
- **Tick制生活模拟**：基于需求系统的自主决策，角色会饿、会累、会孤独
- **关系演化**：友谊、恋爱、对立——关系由记忆和互动自然发展
- **社区共享**：公开画廊、跨用户互动、支持Toyhouse角色导入

## 特性 (Features)

### 角色系统
- **Big Five人格模型** — 开放性、尽责性、外向性、宜人性、神经质五大维度精细调节
- **可定制外貌** — 详细的外观描述与立绘上传
- **技能树** — 烹饪、绘画、编程、社交等多种可成长技能
- **背景与Lore** — 丰富的角色背景故事和世界观设定

### 模拟引擎
- **Tick制时间系统** — 可调速的模拟时钟，从实时到快进自由切换
- **6大核心需求** — 饥饿、精力、社交、娱乐、卫生、舒适
- **15+日常活动** — 做饭、吃饭、睡觉、聊天、工作、阅读、锻炼等
- **自主决策引擎** — 角色根据性格和当前需求自主选择行为

### AI驱动
- **三层混合架构**
  - **Claude API** — 用于关键剧情场景、重大决策和深度对话
  - **Ollama本地模型** — 用于日常对话和一般性互动，零API成本
  - **规则引擎** — 用于基础行为逻辑，确保系统稳定高效运行

### 关系系统
- **多维度关系** — 友谊值、浪漫值、对立值独立追踪
- **记忆驱动互动** — 角色会记住过去的互动，并影响未来的行为
- **关系事件** — 告白、争吵、和好等自然触发的关系事件

### 社区功能
- **公开角色画廊** — 展示你的OC，浏览其他创作者的角色
- **跨用户互动** — 经授权后，不同用户的角色可以在同一世界互动
- **Toyhouse导入** — 支持从Toyhouse平台导入已有的OC数据

## 技术栈 (Tech Stack)

| 层级 | 技术 | 用途 |
|------|------|------|
| **后端框架** | FastAPI | 异步 REST API 服务 |
| **模拟引擎** | SimPy | 离散事件驱动的生活模拟 |
| **ORM** | SQLAlchemy 2.0 | 异步数据库访问层 |
| **数据库** | PostgreSQL 16 | 主数据存储 |
| **缓存** | Redis | 会话管理与模拟状态缓存 |
| **前端框架** | React 18 | 用户界面 |
| **游戏渲染** | Phaser 3 | 2D模拟场景渲染 |
| **状态管理** | Zustand | 轻量前端状态管理 |
| **类型系统** | TypeScript 5 | 前端类型安全 |
| **容器化** | Docker & Compose | 一键部署与开发环境 |

## 快速开始 (Quick Start)

### 使用 Docker（推荐）

```bash
# 克隆仓库
git clone https://github.com/the-world-sim/the-world.git
cd the-world

# 复制环境变量文件并根据需要修改
cp .env.example .env

# 一键启动所有服务
docker-compose up -d
```

启动完成后访问：

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

### 手动安装（不使用 Docker）

#### 后端

```bash
# 确保已安装 Python 3.12+ 和 uv
cd backend

# 使用 uv 创建虚拟环境并安装依赖
uv sync

# 初始化数据库
uv run alembic upgrade head

# 启动开发服务器
uv run uvicorn app.main:app --reload --port 8000
```

#### 前端

```bash
# 确保已安装 Node.js 20+ 和 pnpm
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 环境变量

在 `.env` 文件中配置以下关键变量：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/the_world

# Redis
REDIS_URL=redis://localhost:6379/0

# AI 服务（可选 - 不配置则仅使用规则引擎）
ANTHROPIC_API_KEY=your-api-key
OLLAMA_BASE_URL=http://localhost:11434
```

## 项目结构 (Project Structure)

```
the-world/
├── backend/                  # Python 后端
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/          # Pydantic 模式
│   │   ├── services/         # 业务逻辑
│   │   ├── simulation/       # SimPy 模拟引擎
│   │   │   ├── engine.py     # 主引擎循环
│   │   │   ├── needs.py      # 需求系统
│   │   │   ├── activities.py # 活动定义
│   │   │   └── ai/           # AI 决策层
│   │   └── main.py           # 应用入口
│   ├── tests/                # 后端测试
│   ├── alembic/              # 数据库迁移
│   └── pyproject.toml
├── frontend/                 # React + TypeScript 前端
│   ├── src/
│   │   ├── components/       # React 组件
│   │   ├── pages/            # 页面
│   │   ├── stores/           # Zustand 状态
│   │   ├── game/             # Phaser 游戏场景
│   │   ├── api/              # API 客户端
│   │   └── types/            # TypeScript 类型
│   ├── public/
│   └── package.json
├── shared/                   # 前后端共享定义
├── docs/                     # 项目文档
├── docker-compose.yml
├── Makefile
└── README.md
```

## 关键文档

- [API 契约基线](docs/api_contract.md)（前后端联调与回归测试参考）
- [手工 UAT 清单](docs/UAT_manual_checklist.md)（发版前高拟真验收步骤）

## 开发路线图 (Roadmap)

### Phase 0 - 基础设施 🏗️
- [x] 项目初始化与仓库搭建
- [x] CI/CD 流水线配置
- [ ] Docker 开发环境
- [ ] 数据库 Schema 设计

### Phase 1 - 核心角色系统 👤
- [x] 角色CRUD API
- [x] Big Five 人格模型
- [ ] 角色外貌与立绘系统
- [x] 角色创建前端界面

### Phase 2 - 模拟引擎 ⚙️
- [x] SimPy Tick 引擎
- [x] 6大需求系统
- [x] 基础活动集（吃饭、睡觉、社交等）
- [x] 规则引擎决策层

### Phase 3 - AI集成 🧠
- [x] Ollama 本地对话集成
- [x] Claude API 关键场景集成
- [x] 三层降级策略
- [x] 对话记忆系统

### Phase 4 - 关系与互动 💬
- [x] 关系数值追踪
- [x] 记忆系统
- [x] 关系事件触发器
- [x] NPC互动逻辑

### Phase 5 - 社区功能 🌐
- [x] 公开角色画廊
- [x] 用户认证与授权
- [ ] 跨用户互动
- [ ] Toyhouse 导入

### Phase 6 - 打磨与扩展 ✨
- [ ] 自定义地图编辑器
- [ ] 物品与经济系统
- [ ] 成就系统
- [ ] 移动端适配

## 贡献指南 (Contributing)

我们欢迎所有形式的贡献！无论是提交Bug报告、提出新功能建议，还是直接贡献代码，都是对项目的巨大帮助。

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献流程、代码规范和开发指南。

在参与本项目之前，请确保你已阅读并同意遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。

## 许可证 (License)

本项目基于 [MIT 许可证](LICENSE) 开源。

你可以自由地使用、修改和分发本项目，只需保留版权声明即可。

---

<div align="center">

**用爱构建，为创作者而生。**

如果这个项目对你有帮助，请给我们一个 Star 吧！

</div>
