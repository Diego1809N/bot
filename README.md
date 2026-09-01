# BTCUSDT Scalper Web App

Web app para ejecutar/backtestear un scalper de BTCUSDT Futures. Incluye:
- FastAPI backend
- React + Vite frontend
- Motor de señales por score
- Modo PAPER por defecto
- Modo LIVE opcional mediante Binance Futures REST/WebSocket
- Dashboard en tiempo real
- TP/SL y trailing configurables
- Registro de operaciones en SQLite
- Dockerfile y docker-compose
- API docs en `/docs`

## 1. Requisitos

- Python 3.12+
- Node.js 20+
- npm
- Docker opcional

## 2. Configuración

Copia `.env.example` a `.env`.

Para PAPER no necesitas API keys.

Para LIVE:
- `BINANCE_API_KEY=...`
- `BINANCE_API_SECRET=...`
- `BINANCE_TESTNET=true` para pruebas en Binance Futures Testnet.
- `BINANCE_TESTNET=false` para cuenta real.

El backend nunca expone el secret al frontend.

## 3. Ejecutar en desarrollo

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre la URL que muestre Vite.

## 4. Ejecutar todo con Docker

```bash
docker compose up --build
```

La app queda en `http://localhost:8000`.

## 5. Operación

El modo PAPER viene activado por defecto. El bot usa:
- BTCUSDT
- 1m
- EMA 20 / 50 / 200
- RSI
- ADX/DI
- momentum
- volumen relativo
- score configurable
- TP/SL por porcentaje
- trailing opcional

La frecuencia se controla principalmente con `ENTRY_SCORE` y `COOLDOWN_SECONDS`.

Para LIVE, configura las credenciales y activa el modo LIVE desde el panel.

## 6. Diseño

FastAPI puede servir el build estático del frontend, por lo que el despliegue puede hacerse como una sola aplicación. La documentación oficial de FastAPI contempla este patrón de servir frontend estático desde la aplicación.

## 7. Nota técnica

El motor está deliberadamente separado de la UI y del adaptador de exchange:
- `strategy.py`: señales
- `engine.py`: ciclo de trading
- `binance.py`: comunicación con Binance
- `models.py`: persistencia
- `main.py`: API/WebSocket
