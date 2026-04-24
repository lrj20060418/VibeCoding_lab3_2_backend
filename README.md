# Backend（FastAPI）

## 运行（Windows / PowerShell）

建议使用虚拟环境：

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

验证：

- 打开 `http://127.0.0.1:8000/health`  
  期望返回：`{"ok": true}`

