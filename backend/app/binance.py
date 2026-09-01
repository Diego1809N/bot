import hashlib
import hmac
import time
from urllib.parse import urlencode
import httpx
import websockets
import json


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
        self.ws_base = "wss://stream.binancefuture.com/ws" if testnet else "wss://fstream.binance.com/ws"

    async def public(self, path: str, params: dict | None = None):
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(self.base + path, params=params or {})
            r.raise_for_status()
            return r.json()

    async def signed(self, method: str, path: str, params: dict | None = None):
        if not self.api_key or not self.api_secret:
            raise RuntimeError("BINANCE_API_KEY/BINANCE_API_SECRET no configuradas")

        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params, doseq=True)
        signature = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = signature

        headers = {"X-MBX-APIKEY": self.api_key}
        async with httpx.AsyncClient(timeout=10) as client:
            request = getattr(client, method.lower())
            r = await request(self.base + path, params=params, headers=headers)
            r.raise_for_status()
            return r.json()

    async def klines(self, symbol: str, interval: str, limit: int = 300):
        return await self.public("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})

    async def price(self, symbol: str):
        return await self.public("/fapi/v1/ticker/price", {"symbol": symbol})

    async def set_leverage(self, symbol: str, leverage: int):
        return await self.signed("POST", "/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage})

    async def order_market(self, symbol: str, side: str, quantity: float, reduce_only: bool = False):
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": self._fmt(quantity),
        }
        if reduce_only:
            params["reduceOnly"] = "true"
        return await self.signed("POST", "/fapi/v1/order", params)

    async def account(self):
        return await self.signed("GET", "/fapi/v2/account")

    @staticmethod
    def _fmt(x: float) -> str:
        return f"{x:.6f}".rstrip("0").rstrip(".")


async def stream_mark_price(symbol: str):
    url = f"wss://fstream.binance.com/ws/{symbol.lower()}@markPrice@1s"
    async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
        async for message in ws:
            yield json.loads(message)
