import pandas as pd
from .indicators import ema, rsi, adx_di, atr


def build_signal(df: pd.DataFrame, cfg: dict) -> dict:
    d = df.copy()
    d["ema_fast"] = ema(d.close, cfg["ema_fast"])
    d["ema_mid"] = ema(d.close, cfg["ema_mid"])
    d["ema_slow"] = ema(d.close, cfg["ema_slow"])
    d["rsi"] = rsi(d.close, cfg["rsi_length"])
    d["adx"], d["plus_di"], d["minus_di"] = adx_di(d, cfg["adx_length"])
    d["atr"] = atr(d, cfg["adx_length"])
    d["momentum"] = d.close.pct_change(cfg["momentum_length"]) * 100
    d["vol_avg"] = d.volume.rolling(cfg["volume_length"]).mean()
    d["vol_ratio"] = d.volume / d.vol_avg

    x = d.iloc[-1]
    long_score = 0
    short_score = 0

    if x.ema_fast > x.ema_mid: long_score += 2
    if x.ema_fast < x.ema_mid: short_score += 2
    if x.close > x.ema_fast: long_score += 1
    if x.close < x.ema_fast: short_score += 1
    if x.rsi >= 50: long_score += 1
    if x.rsi <= 50: short_score += 1
    if x.plus_di > x.minus_di: long_score += 1
    if x.minus_di > x.plus_di: short_score += 1
    if x.momentum > 0: long_score += 2
    if x.momentum < 0: short_score += 2
    if x.adx >= 15:
        if x.plus_di > x.minus_di: long_score += 1
        if x.minus_di > x.plus_di: short_score += 1
    if x.vol_ratio >= 1.0:
        if x.close >= x.ema_fast: long_score += 1
        if x.close <= x.ema_fast: short_score += 1

    threshold = cfg["entry_score"]
    if long_score >= threshold and long_score > short_score:
        side = "LONG"
    elif short_score >= threshold and short_score > long_score:
        side = "SHORT"
    else:
        side = "NONE"

    return {
        "side": side,
        "long_score": int(long_score),
        "short_score": int(short_score),
        "price": float(x.close),
        "rsi": float(x.rsi),
        "adx": float(x.adx),
        "momentum": float(x.momentum),
        "atr": float(x.atr),
        "volume_ratio": float(x.vol_ratio),
        "ema_fast": float(x.ema_fast),
        "ema_mid": float(x.ema_mid),
        "ema_slow": float(x.ema_slow),
    }
