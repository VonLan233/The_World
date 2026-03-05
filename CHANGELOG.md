# Changelog / 更新日志

本文件记录项目的所有重要变更。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Fixed / 修复
- 统一角色更新接口契约：`/api/v1/characters/{id}` 现同时支持 `PUT` 与 `PATCH`，避免前后端方法不一致导致的联调失败。

### Tests / 测试
- 新增角色接口回归用例，覆盖 `PATCH /api/v1/characters/{id}` 的部分字段更新场景。
- 新增最小链路联调验收测试：登录 → 创建角色 → 更新角色 → 创建世界 → 启动/调速/读取模拟状态。
- 新增 OpenAPI 契约守卫测试，锁定核心路径与 HTTP 方法（含登录表单协议约束）。

### Docs / 文档
- 新增 API 契约基线文档：`docs/api_contract.md`，统一记录 REST/WS 关键接口与最小链路验收范围。

## [0.1.0] - 2025-01-01

### Added / 新增
- 项目初始化
- 基础项目结构搭建（前端 + 后端 + 共享模块）
- 开发环境配置（Docker Compose、Makefile）
- CI/CD 流水线配置（GitHub Actions）
- 项目文档（README、贡献指南、行为准则）
- Issue 模板和 PR 模板
- MIT 开源许可证

[Unreleased]: https://github.com/the-world-sim/the-world/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/the-world-sim/the-world/releases/tag/v0.1.0
