# Backend（FastAPI）

## 运行（Windows / PowerShell）

建议使用虚拟环境：

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

验证：

- 打开 `http://127.0.0.1:8000/health`  
  期望返回：`{"ok": true}`

## V2：规划 CRUD（SQLite 持久化）

### 规划接口

- `POST /api/plans` 创建规划
- `GET /api/plans` 规划列表
- `GET /api/plans/{plan_id}` 规划详情
- `PUT /api/plans/{plan_id}` 更新规划（部分更新）

### 快速测试（示例）

创建：

```bash
curl -X POST http://127.0.0.1:8000/api/plans ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"周末出行\",\"date\":\"2026-04-26\",\"budget\":500,\"people_count\":2,\"preferences\":\"轻松一点\"}"
```

列表：

```bash
curl http://127.0.0.1:8000/api/plans
```

详情（把 PLAN_ID 替换成上一步返回的 id）：

```bash
curl http://127.0.0.1:8000/api/plans/PLAN_ID
```

更新（部分字段即可）：

```bash
curl -X PUT http://127.0.0.1:8000/api/plans/PLAN_ID ^
  -H "Content-Type: application/json" ^
  -d "{\"budget\":800}"
```

