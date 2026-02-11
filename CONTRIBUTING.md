# 贡献指南 (Contributing Guide)

感谢你有兴趣为 **The World（世界）** 做出贡献！本文档将帮助你了解如何参与项目开发。

## 目录

- [开发环境搭建](#开发环境搭建)
- [分支命名规范](#分支命名规范)
- [提交信息规范](#提交信息规范)
- [Pull Request 流程](#pull-request-流程)
- [代码风格](#代码风格)
- [测试要求](#测试要求)
- [Code Review 流程](#code-review-流程)

---

## 开发环境搭建

### 前置要求

- **Python** 3.12+
- **Node.js** 20+
- **uv**（Python 包管理器）
- **pnpm**（Node.js 包管理器）
- **Docker** 和 **Docker Compose**（可选，用于运行 PostgreSQL 和 Redis）
- **Git**

### 步骤

1. **Fork 仓库** 并克隆到本地：

```bash
git clone https://github.com/<your-username>/the-world.git
cd the-world
```

2. **添加上游仓库**：

```bash
git remote add upstream https://github.com/the-world-sim/the-world.git
```

3. **启动基础设施服务**（PostgreSQL、Redis）：

```bash
docker-compose up -d postgres redis
```

4. **后端环境**：

```bash
cd backend
uv sync                         # 安装依赖
uv run alembic upgrade head     # 初始化数据库
uv run uvicorn app.main:app --reload --port 8000  # 启动开发服务器
```

5. **前端环境**：

```bash
cd frontend
pnpm install     # 安装依赖
pnpm dev         # 启动开发服务器
```

6. **验证环境**：
   - 后端 API 文档：http://localhost:8000/docs
   - 前端界面：http://localhost:3000

---

## 分支命名规范

从 `main` 分支创建新分支，命名遵循以下格式：

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feature/` | 新功能开发 | `feature/character-creation` |
| `fix/` | Bug 修复 | `fix/need-calculation-overflow` |
| `docs/` | 文档更新 | `docs/api-endpoint-guide` |
| `refactor/` | 代码重构 | `refactor/simulation-engine` |
| `test/` | 测试相关 | `test/relationship-service` |
| `chore/` | 构建/工具/依赖更新 | `chore/upgrade-fastapi` |

```bash
# 示例：创建一个新功能分支
git checkout main
git pull upstream main
git checkout -b feature/character-creation
```

---

## 提交信息规范

本项目遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

### 格式

```
<类型>(<作用域>): <简短描述>

<可选的详细描述>

<可选的脚注>
```

### 类型

| 类型 | 描述 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `refactor` | 代码重构（不影响功能） |
| `test` | 添加或修改测试 |
| `chore` | 构建过程、辅助工具或依赖的变动 |
| `style` | 代码格式调整（不影响逻辑） |
| `perf` | 性能优化 |
| `ci` | CI/CD 配置变更 |

### 示例

```
feat(character): 添加Big Five人格模型

实现了基于Big Five的人格系统，包括：
- 五大维度的数值设置（0-100）
- 人格特征对行为决策的影响权重
- 人格档案的持久化存储

Closes #42
```

```
fix(simulation): 修复需求值溢出导致的崩溃

当角色需求值降至负数时，模拟引擎会抛出异常。
添加了下限检查，确保需求值最低为0。

Fixes #57
```

---

## Pull Request 流程

### 1. 创建 Issue

在开始工作之前，请先创建一个 Issue 描述你想做的事情，或者在已有的 Issue 下留言表示你想负责该任务。这可以避免重复工作。

### 2. Fork 并创建分支

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### 3. 开发与提交

- 按照代码风格规范编写代码
- 编写或更新相关测试
- 确保所有测试通过
- 按照提交规范提交代码

### 4. 保持同步

```bash
git fetch upstream
git rebase upstream/main
```

### 5. 推送并创建 PR

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request，填写 PR 模板中的各项内容。

### 6. 等待 Review

- 维护者会在 1-3 个工作日内进行 Review
- 根据反馈修改代码（在同一分支上继续提交即可）
- 所有 CI 检查通过且至少获得一位维护者批准后，PR 将被合并

---

## 代码风格

### Python（后端）

- **格式化与检查工具**：[Ruff](https://github.com/astral-sh/ruff)
- **类型检查**：[mypy](https://mypy-lang.org/)（strict 模式）
- **关键规则**：
  - 使用 `async/await` 进行异步操作
  - 所有函数参数和返回值必须有类型注解
  - 字符串使用双引号
  - 行宽限制 88 字符

```bash
# 运行格式化
uv run ruff format .

# 运行 lint 检查
uv run ruff check .

# 运行类型检查
uv run mypy .
```

### TypeScript（前端）

- **格式化工具**：[Prettier](https://prettier.io/)
- **检查工具**：[ESLint](https://eslint.org/)
- **关键规则**：
  - 严格的 TypeScript 类型（no `any`）
  - 函数组件 + Hooks 模式
  - 使用命名导出（Named Exports）

```bash
# 运行 lint 检查
pnpm lint

# 运行类型检查
pnpm typecheck

# 运行格式化
pnpm format
```

---

## 测试要求

- **新功能必须附带测试**，没有测试的功能 PR 将不会被合并
- **Bug 修复应附带回归测试**，确保问题不会复现
- 测试覆盖率不得低于现有水平

### 后端测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_character.py

# 查看覆盖率报告
uv run pytest --cov=app --cov-report=html
```

### 前端测试

```bash
# 运行所有测试
pnpm test

# 监视模式
pnpm test:watch

# 查看覆盖率
pnpm test:coverage
```

---

## Code Review 流程

### 对于贡献者

- 确保 PR 描述清楚地解释了**做了什么**和**为什么这样做**
- 及时回复 Review 意见
- 对于不同意的反馈，请礼貌地讨论

### 对于 Reviewer

- 在 1-3 个工作日内完成 Review
- 提供建设性的反馈，解释**为什么**建议修改
- 区分"必须修改"（blocking）和"建议修改"（non-blocking）
- 对好的实现给予肯定

### 合并标准

- 所有 CI 检查通过
- 至少一位维护者批准
- 没有未解决的 blocking 反馈
- 分支已与 `main` 同步

---

## 需要帮助？

- 查看 [Issues](https://github.com/the-world-sim/the-world/issues) 中标记为 `good first issue` 的任务
- 在 Issue 或 Discussion 中提问
- 阅读 [项目文档](docs/)

感谢你的贡献，让我们一起把 The World 做得更好！
