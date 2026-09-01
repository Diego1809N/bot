import pandas as pd
import numpy as np
from app.strategy import build_signal

def test_strategy_returns_signal():
    n = 300
    close = np.linspace(80000, 81000, n) + np.sin(np.arange(n))*20
    df = pd.DataFrame({
        "close": close,
        "open": close,
        "high": close + 10,
        "low": close - 10,
        "volume": np.ones(n) * 100
    })
    cfg = {
        "ema_fast":20,"ema_mid":50,"ema_slow":200,"rsi_length":14,
        "adx_length":14,"momentum_length":5,"volume_length":20,"entry_score":5
    }
    result = build_signal(df, cfg)
    assert result["side"] in {"LONG","SHORT","NONE"}
    assert "long_score" in result and "short_score" in result
