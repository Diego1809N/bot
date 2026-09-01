from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .config import settings
from .db import init_db
from .engine import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    await engine.stop()


app = FastAPI(title="BTCUSDT Scalper", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/status")
async def status():
    return engine.snapshot()


@app.post("/api/bot/start")
async def start_bot():
    await engine.start()
    return engine.snapshot()


@app.post("/api/bot/stop")
async def stop_bot():
    await engine.stop()
    return engine.snapshot()


@app.get("/api/trades")
async def trades():
    from .db import SessionLocal
    from .models import Trade
    db = SessionLocal()
    try:
        rows = db.query(Trade).order_by(Trade.id.desc()).limit(100).all()
        return [{
            "id": x.id, "symbol": x.symbol, "side": x.side, "mode": x.mode,
            "entry_price": x.entry_price, "exit_price": x.exit_price,
            "quantity": x.quantity, "pnl": x.pnl, "score": x.score,
            "status": x.status, "opened_at": x.opened_at, "closed_at": x.closed_at
        } for x in rows]
    finally:
        db.close()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json(engine.snapshot())
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


dist = Path(__file__).resolve().parents[2] / "dist"
if dist.exists():
    @app.get("/{path:path}")
    async def frontend(path: str):
        target = dist / path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(dist / "index.html")
