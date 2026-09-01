import React, {useEffect, useState} from 'react'
import {createRoot} from 'react-dom/client'
import {Play, Square, Activity, TrendingUp, TrendingDown} from 'lucide-react'
import './style.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [s, setS] = useState(null)
  const [trades, setTrades] = useState([])
  const [busy, setBusy] = useState(false)

  const load = async () => {
    const [a,b] = await Promise.all([
      fetch(`${API}/api/status`).then(r=>r.json()),
      fetch(`${API}/api/trades`).then(r=>r.json())
    ])
    setS(a); setTrades(b)
  }

  useEffect(() => {
    load()
    const timer = setInterval(load, 1500)
    return () => clearInterval(timer)
  }, [])

  const action = async (path) => {
    setBusy(true)
    try {
      await fetch(`${API}${path}`, {method:'POST'})
      await load()
    } finally { setBusy(false) }
  }

  if (!s) return <div className="loading">Conectando...</div>
  const sig = s.signal || {}
  const pnl = Number(s.stats?.pnl || 0)
  const side = sig.side || 'NONE'

  return <div className="app">
    <header>
      <div>
        <h1>BTCUSDT <span>SCALPER</span></h1>
        <p>High-frequency signal engine · {s.config.timeframe} · {s.config.leverage}x</p>
      </div>
      <div className={`status ${s.running?'on':'off'}`}>
        <i/> {s.running?'RUNNING':'STOPPED'}
      </div>
    </header>

    <section className="controls">
      <button disabled={busy || s.running} onClick={()=>action('/api/bot/start')}><Play size={17}/> Iniciar</button>
      <button className="danger" disabled={busy || !s.running} onClick={()=>action('/api/bot/stop')}><Square size={17}/> Detener</button>
      <div className="mode">MODE <b>{s.config.mode}</b></div>
    </section>

    <main>
      <div className="grid">
        <Card title="Precio" value={`$${Number(sig.price||0).toLocaleString(undefined,{maximumFractionDigits:2})}`} sub="Mark/close"/>
        <Card title="Señal" value={side} sub={`L ${sig.long_score||0} · S ${sig.short_score||0}`} icon={side==='LONG'?<TrendingUp/>:side==='SHORT'?<TrendingDown/>:<Activity/>}/>
        <Card title="PnL" value={`${pnl>=0?'+':''}$${pnl.toFixed(4)}`} sub={`${s.stats.trades} operaciones`}/>
        <Card title="Posición" value={s.position ? s.position.side : '—'} sub={s.position ? `Entrada $${s.position.entry.toFixed(2)}` : 'Sin posición'}/>
      </div>

      <div className="two">
        <section className="panel">
          <h2>Indicadores</h2>
          <div className="metrics">
            <Metric n="RSI" v={fmt(sig.rsi)}/>
            <Metric n="ADX" v={fmt(sig.adx)}/>
            <Metric n="Momentum" v={`${fmt(sig.momentum)}%`}/>
            <Metric n="Volumen" v={`${fmt(sig.volume_ratio)}x`}/>
            <Metric n="EMA 20" v={fmt(sig.ema_fast)}/>
            <Metric n="EMA 50" v={fmt(sig.ema_mid)}/>
            <Metric n="EMA 200" v={fmt(sig.ema_slow)}/>
          </div>
        </section>

        <section className="panel">
          <h2>Configuración</h2>
          <div className="metrics">
            <Metric n="Entry score" v={s.config.entry_score}/>
            <Metric n="Position" v={`$${s.config.position_usdt}`}/>
            <Metric n="TP" v={`${s.config.tp_percent}%`}/>
            <Metric n="SL" v={`${s.config.sl_percent}%`}/>
            <Metric n="Trailing" v={s.config.trailing_enabled?'ON':'OFF'}/>
            <Metric n="Cooldown" v={`${s.config.cooldown_seconds}s`}/>
          </div>
        </section>
      </div>

      <section className="panel">
        <h2>Últimas operaciones</h2>
        <div className="table">
          <div className="tr head"><span>Hora</span><span>Side</span><span>Entrada</span><span>Salida</span><span>Score</span><span>PnL</span></div>
          {trades.map(t=><div className="tr" key={t.id}>
            <span>{new Date(t.opened_at).toLocaleTimeString()}</span>
            <span className={t.side==='LONG'?'long':'short'}>{t.side}</span>
            <span>{Number(t.entry_price).toFixed(2)}</span>
            <span>{t.exit_price?Number(t.exit_price).toFixed(2):'OPEN'}</span>
            <span>{t.score}</span>
            <span className={(t.pnl||0)>=0?'profit':'loss'}>{t.pnl==null?'—':`${t.pnl>=0?'+':''}${Number(t.pnl).toFixed(4)}`}</span>
          </div>)}
        </div>
      </section>
    </main>
  </div>
}

function Card({title,value,sub,icon}) {
  return <div className="card"><div className="label">{title}</div><div className="value">{icon}<strong>{value}</strong></div><small>{sub}</small></div>
}
function Metric({n,v}) { return <div className="metric"><span>{n}</span><b>{v}</b></div> }
function fmt(x) { return Number.isFinite(Number(x)) ? Number(x).toFixed(2) : '—' }

createRoot(document.getElementById('root')).render(<App/>)
