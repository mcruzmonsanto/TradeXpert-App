# config.py
# --- CONFIGURACIÓN GLOBAL DEL BOT ---
import os
import streamlit as st

# Intentamos leer de Streamlit Secrets (Nube), si falla, leemos de variables de entorno (Local)
def get_secret(key):
    if hasattr(st, "secrets") and key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, "TOKEN_NO_ENCONTRADO")

# --- CREDENCIALES ---
# YA NO ESCRIBIMOS EL TOKEN AQUÍ DIRECTAMENTE
TELEGRAM_TOKEN = get_secret("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID")

# config.py

# --- UNIVERSO DE ACTIVOS (S&P 500 SECTORS + CRYPTO + INDICES) ---
TICKERS = [
    # --- INDICES PRINCIPALES ---
    "SPY", "QQQ", "DIA",          # S&P 500, Nasdaq 100, Dow Jones

    # --- CRYPTO (TOP 3) ---
    "BTC-USD", "ETH-USD", "SOL-USD",

    # --- TECNOLOGÍA (Tech) ---
    "MSFT", "AAPL", "NVDA",
    
    # --- COMUNICACIONES (Comm Services) ---
    "GOOGL", "META", "NFLX",

    # --- CONSUMO DISCRECIONAL (Cyclical) ---
    "AMZN", "TSLA", "HD",

    # --- FINANCIEROS (Financials) ---
    "JPM", "V", "MA",

    # --- SALUD (Healthcare) ---
    "LLY", "UNH", "JNJ",

    # --- CONSUMO BÁSICO (Defensive) ---
    "WMT", "PG", "COST",

    # --- ENERGÍA (Energy) ---
    "XOM", "CVX", "COP",

    # --- INDUSTRIALES ---
    "CAT", "UNP", "GE",
    
    # --- MATERIALES & UTILITIES ---
    "LIN", "NEE", "SHW"
]

# 2. PARÁMETROS DE ESTRATEGIA (Optimizados)
SMA_FAST = 55            # Media Rápida
SMA_SLOW = 90            # Media Lenta
RSI_THRESHOLD = 70       # Límite de Sobrecompra
STOP_LOSS_PCT = 0.10     # 10% Trailing Stop

# ESTRATEGIA 2: REVERSIÓN A LA MEDIA (CAZAR REBOTES)
RSI_OVERSOLD = 30       # Comprar si RSI baja de 30 (Pánico)
RSI_EXIT_MEAN = 50      # Vender si RSI recupera 50 (Retorno a la media)

# 3. CONFIGURACIÓN DE TIEMPO
START_DATE = "2020-01-01"
END_DATE = "2023-12-30"
INITIAL_CAPITAL = 500

# --- GESTIÓN DE CAPITAL ---
CAPITAL_TOTAL = 1000       # Tu capital total en el Broker (USD)
RIESGO_POR_OPERACION = 0.02 # Arriesgar solo el 2% del capital por trade (Estándar Profesional)
ATR_MULTIPLIER = 1.5        # Qué tan lejos poner el Stop (1.5 veces la volatilidad es normal)
RR_RATIO = 2.0              # Buscamos ganar el doble de lo que arriesgamos
