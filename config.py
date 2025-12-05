# config.py
# --- CONFIGURACIÓN GLOBAL DEL BOT ---

# 1. LISTA DE ACTIVOS (Portafolio)
TICKERS = ["AMD", "NVDA", "MSFT", "GOOGL", "TSLA"]

# 2. PARÁMETROS DE ESTRATEGIA (Optimizados)
SMA_FAST = 55            # Media Rápida
SMA_SLOW = 90            # Media Lenta
RSI_THRESHOLD = 70       # Límite de Sobrecompra
STOP_LOSS_PCT = 0.10     # 10% Trailing Stop

# 3. CONFIGURACIÓN DE TIEMPO
START_DATE = "2020-01-01"
END_DATE = "2023-12-30"
INITIAL_CAPITAL = 500

# 4. CREDENCIALES DE TELEGRAM (¡Sin espacios al inicio!)
# El token debe ir entre comillas
TELEGRAM_TOKEN = "8579707511:AAFkItAYRefwmRMkqRBf_A_jcruvce4EVyU"
TELEGRAM_CHAT_ID = "7277947502"