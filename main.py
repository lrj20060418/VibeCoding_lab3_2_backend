from fastapi import FastAPI

app = FastAPI(title="Lab 3-2 Backend", version="0.1.0")


@app.get("/health")
def health():
    return {"ok": True}

