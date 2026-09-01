import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import pandas as pd
from .binance import BinanceClient
from .strategy import build_signal
from .config import settings
from .db import SessionLocal
from .models import Trade


@dataclass
class Position:
    side: str
    entry: float
    quantity: float
    score: int
    peak: float


class TradingEngine:
    def __init__(self):
        self.running = False
        self.task = None
        self.client = BinanceClient(settings.binance_api_key, settings.binance_api_secret, settings.binance_testnet)
        self.position: Position | None = None
        self.last_signal = {}
        self.last_trade_time = 0.0
        self.stats = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0.0}

    async def start(self):
        if self.running:
            return
        self.running = True
        if settings.mode == "LIVE":
            await self.client.set_leverage(settings.symbol, settings.leverage)
        self.task = asyncio.create_task(self.loop())

    async def stop(self):
        self.running = False
        if self.task:
            await self.task
            self.task = None

    async def loop(self):
        while self.running:
            try:
                klines = await self.client.klines(settings.symbol, settings.timeframe, 300)
                df = pd.DataFrame(klines, columns=[
                    "open_time","open","high","low","close","volume","close_time",
                    "quote_volume","trades","taker_base","taker_quote","ignore"
                ])
                for c in ["open","high","low","close","volume"]:
                    df[c] = pd.to_numeric(df[c])
                signal = build_signal(df, self.cfg())
                self.last_signal = signal

                price = float(signal["price"])
                await self.manage_position(price, signal)

                if self.position is None and signal["side"] != "NONE":
                    await self.open_position(signal)

            except Exception as exc:
                self.last_signal["error"] = str(exc)
            await asyncio.sleep(1)

    def cfg(self):
        return {
            "ema_fast": settings.ema_fast, "ema_mid": settings.ema_mid, "ema_slow": settings.ema_slow,
            "rsi_length": settings.rsi_length, "adx_length": settings.adx_length,
            "momentum_length": settings.momentum_length, "volume_length": settings.volume_length,
            "entry_score": settings.entry_score,
        }

    async def open_position(self, signal):
        import time
        if time.time() - self.last_trade_time < settings.cooldown_seconds:
            return
        price = signal["price"]
        qty = settings.position_usdt / price
        side = signal["side"]
        if settings.mode == "LIVE":
            await self.client.order_market(settings.symbol, "BUY" if side == "LONG" else "SELL", qty)
        self.position = Position(side, price, qty, max(signal["long_score"], signal["short_score"]), price)
        self.last_trade_time = time.time()
        self._save_open()

    async def manage_position(self, price, signal):
        if not self.position:
            return
        p = self.position
        if p.side == "LONG":
            p.peak = max(p.peak, price)
            change = (price - p.entry) / p.entry * 100
            trailing_hit = settings.trailing_enabled and change >= settings.trailing_activation_percent and price <= p.peak * (1 - settings.trailing_distance_percent / 100)
            exit_hit = change >= settings.tp_percent or change <= -settings.sl_percent or trailing_hit
            exit_side = "SELL"
        else:
            p.peak = min(p.peak, price)
            change = (p.entry - price) / p.entry * 100
            trailing_hit = settings.trailing_enabled and change >= settings.trailing_activation_percent and price >= p.peak * (1 + settings.trailing_distance_percent / 100)
            exit_hit = change >= settings.tp_percent or change <= -settings.sl_percent or trailing_hit
            exit_side = "BUY"

        if exit_hit:
            if settings.mode == "LIVE":
                await self.client.order_market(settings.symbol, exit_side, p.quantity, reduce_only=True)
            pnl = p.quantity * (price - p.entry) if p.side == "LONG" else p.quantity * (p.entry - price)
            self.stats["trades"] += 1
            self.stats["pnl"] += pnl
            self.stats["wins" if pnl >= 0 else "losses"] += 1
            self._close_last(price, pnl)
            self.position = None

    def _save_open(self):
        db = SessionLocal()
        try:
            db.add(Trade(symbol=settings.symbol, side=self.position.side, mode=settings.mode,
                         entry_price=self.position.entry, quantity=self.position.quantity,
                         score=self.position.score, status="OPEN"))
            db.commit()
        finally:
            db.close()

    def _close_last(self, price, pnl):
        db = SessionLocal()
        try:
            trade = db.query(Trade).filter(Trade.status == "OPEN").order_by(Trade.id.desc()).first()
            if trade:
                trade.exit_price = price
                trade.pnl = pnl
                trade.status = "CLOSED"
                trade.closed_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()

    def cfg_snapshot(self):
        return {
            "symbol": settings.symbol, "leverage": settings.leverage, "timeframe": settings.timeframe,
            "mode": settings.mode, "entry_score": settings.entry_score,
            "position_usdt": settings.position_usdt, "tp_percent": settings.tp_percent,
            "sl_percent": settings.sl_percent, "trailing_enabled": settings.trailing_enabled,
            "cooldown_seconds": settings.cooldown_seconds
        }

    def snapshot(self):
        return {
            "running": self.running,
            "config": self.cfg_snapshot(),
            "signal": self.last_signal,
            "position": asdict(self.position) if self.position else None,
            "stats": self.stats,
        }


engine = TradingEngine()
