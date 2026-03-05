# The World API 契约清单（P0 稳定基线）

> 更新日期：2026-03-04  
> 目的：为前后端联调、回归测试与 CI 守卫提供单一事实来源。

## 约定

- REST 基础前缀：`/api/v1`
- 认证方式：`Authorization: Bearer <token>`
- 字段命名：JSON 使用 `camelCase`
- 健康检查端点不在 `/api/v1` 下：`GET /health`
- 角色更新兼容：`PUT` 与 `PATCH` 均可用于 `/api/v1/characters/{character_id}`

---

## 认证（Auth）

### `POST /api/v1/auth/register`
- **请求体（JSON）**：`username`, `email`, `password`, `displayName?`
- **成功响应**：`201`
- **响应体**：`{ access_token, token_type, user }`
- **常见错误**：
  - `409` 用户名或邮箱重复
  - `422` 密码强度不满足要求

### `POST /api/v1/auth/login`
- **请求体**：`application/x-www-form-urlencoded`
  - `username`, `password`
- **成功响应**：`200`
- **响应体**：`{ access_token, token_type, user }`
- **常见错误**：
  - `401` 用户名或密码错误
  - `429` 登录限流

### `GET /api/v1/auth/me`
- **鉴权**：需要 Bearer Token
- **成功响应**：`200`
- **响应体**：`UserResponse`
- **常见错误**：`401`

---

## 角色（Characters）

### `POST /api/v1/characters/`
- **鉴权**：需要
- **请求体（JSON）**：`CharacterCreate`
- **成功响应**：`201`
- **响应体**：`CharacterResponse`

### `GET /api/v1/characters/`
- **鉴权**：需要
- **成功响应**：`200`
- **响应体**：`CharacterResponse[]`（当前用户拥有）

### `GET /api/v1/characters/public`
- **鉴权**：不需要
- **查询参数**：`limit?`, `offset?`
- **成功响应**：`200`
- **响应体**：`CharacterResponse[]`（仅公开角色）

### `GET /api/v1/characters/{character_id}`
- **鉴权**：当前实现可匿名读取（若不存在返回 `404`）
- **成功响应**：`200`
- **响应体**：`CharacterResponse`

### `PUT|PATCH /api/v1/characters/{character_id}`
- **鉴权**：需要，且必须为角色拥有者
- **请求体（JSON）**：`CharacterUpdate`（部分字段更新）
- **成功响应**：`200`
- **响应体**：`CharacterResponse`
- **常见错误**：`403`（非拥有者）、`404`

### `DELETE /api/v1/characters/{character_id}`
- **鉴权**：需要，且必须为角色拥有者
- **成功响应**：`204`
- **常见错误**：`403`、`404`

---

## 世界（Worlds）

### `POST /api/v1/worlds/`
- **鉴权**：需要
- **成功响应**：`201`
- **响应体**：`WorldResponse`（默认 Starter Town）

### `GET /api/v1/worlds/`
- **鉴权**：需要
- **成功响应**：`200`
- **响应体**：`WorldResponse[]`

### `GET /api/v1/worlds/{world_id}`
- **鉴权**：需要，且世界属于当前用户
- **成功响应**：`200`
- **常见错误**：`404`

---

## 模拟（Simulation）

### `POST /api/v1/simulation/{world_id}/start`
- **成功响应**：`200`
- **响应体**：当前引擎状态（含 `worldId`, `clock`, `characters`）
- **常见错误**：`503`（`sim_manager` 未初始化）

### `POST /api/v1/simulation/{world_id}/pause`
- **成功响应**：`200`
- **常见错误**：`404`（该世界未运行）

### `POST /api/v1/simulation/{world_id}/speed`
- **请求体（JSON）**：`{ speed: number }`
- **成功响应**：`200`
- **响应体**：`{ speed }`
- **常见错误**：`404`

### `GET /api/v1/simulation/{world_id}/state`
- **成功响应**：`200`
- **响应体**：当前引擎状态
- **常见错误**：`404`

---

## 关系（Relationships）

### `GET /api/v1/relationships/{character_id}`
- **成功响应**：`200`
- **响应体**：`RelationshipListResponse`

### `GET /api/v1/relationships/{character_id}/{target_id}`
- **成功响应**：`200`
- **响应体**：`RelationshipResponse`
- **常见错误**：`404`（关系不存在）

---

## WebSocket 契约

### 连接地址
- `WS /api/v1/ws/{world_id}`

### 客户端消息（Client -> Server）
- `join_world`
- `leave_world`
- `toggle_simulation`
- `set_speed`
- `place_character`
- `ping`

### 服务端消息（Server -> Client）
- `world_state`
- `character_update`
- `clock_update`
- `simulation_event`
- `character_joined`
- `character_left`
- `dialogue`
- `error`
- `pong`

---

## 最小链路验收（已自动化）

当前最小链路由测试覆盖：
- 登录
- 创建角色
- 更新角色（PATCH）
- 创建世界
- 启动模拟
- 调速
- 读取模拟状态

对应测试文件：`backend/tests/test_api/test_minimal_flow.py`
