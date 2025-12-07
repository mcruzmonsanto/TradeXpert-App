# config.py

# --- UNIVERSO DE ACTIVOS ---
TICKERS = [
    "SPY", "QQQ", "DIA",          # Índices
    "BTC-USD", "ETH-USD", "SOL-USD", # Crypto
    "MSFT", "AAPL", "NVDA",       # Tech
    "GOOGL", "META", "NFLX",      # Comms
    "AMZN", "TSLA", "HD",         # Cyclical
    "JPM", "V", "MA",             # Financials
    "LLY", "UNH", "JNJ",          # Healthcare
    "WMT", "PG", "COST",          # Defensive
    "XOM", "CVX", "COP",          # Energy
    "CAT", "UNP", "GE",           # Industrial
    "LIN", "NEE", "SHW"           # Materials
]

# --- GESTIÓN DE CAPITAL ---
CAPITAL_TOTAL = 10000       
RIESGO_POR_OPERACION = 0.02 
ATR_MULTIPLIER = 1.5        
RR_RATIO = 2.0              

# --- CONFIGURACIONES MAESTRAS (Alpha Map) ---
# Aquí inyectamos la inteligencia que descubrió tu IA
STRATEGY_MAP = {
    # INDICES
    "SPY": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 9, 'slow': 21}},
    "QQQ": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 100}},
    "DIA": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 60}},

    # CRYPTO
    "BTC-USD": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 8, 'slow': 21}},
    "ETH-USD": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 5, 'slow': 13}},
    "SOL-USD": {"strategy": "Bollinger Breakout", "params": {'window': 20, 'std_dev': 2}},

    # TECH
    "MSFT": {"strategy": "Awesome Oscillator", "params": {'fast': 3, 'slow': 10}},
    "AAPL": {"strategy": "Stochastic RSI", "params": {'rsi_period': 9, 'stoch_period': 9, 'k_period': 3, 'd_period': 3}},
    "NVDA": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 100}},

    # COMMS
    "GOOGL": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 100}},
    "META": {"strategy": "Golden Cross (Trend)", "params": {'fast': 20, 'slow': 100}},
    "NFLX": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 100}},

    # CYCLICAL
    "AMZN": {"strategy": "Stochastic RSI", "params": {'rsi_period': 9, 'stoch_period': 9, 'k_period': 3, 'd_period': 3}},
    "TSLA": {"strategy": "MACD Momentum", "params": {'fast': 12, 'slow': 26, 'signal': 9}},
    "HD": {"strategy": "Stochastic RSI", "params": {'rsi_period': 9, 'stoch_period': 9, 'k_period': 3, 'd_period': 3}},

    # FINANCIALS
    "JPM": {"strategy": "Golden Cross (Trend)", "params": {'fast': 20, 'slow': 200}},
    "V": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 60}},
    "MA": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 70}},

    # HEALTHCARE
    "LLY": {"strategy": "Stochastic RSI", "params": {'rsi_period': 9, 'stoch_period': 9, 'k_period': 3, 'd_period': 3}},
    "UNH": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 25, 'rsi_high': 70}},
    "JNJ": {"strategy": "MACD Momentum", "params": {'fast': 12, 'slow': 26, 'signal': 9}},

    # DEFENSIVE
    "WMT": {"strategy": "Golden Cross (Trend)", "params": {'fast': 20, 'slow': 200}},
    "PG": {"strategy": "MACD Momentum", "params": {'fast': 12, 'slow': 26, 'signal': 9}},
    "COST": {"strategy": "Awesome Oscillator", "params": {'fast': 5, 'slow': 34}},

    # ENERGY
    "XOM": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 70}},
    "CVX": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 70}},
    "COP": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 60}},

    # INDUSTRIAL & OTHERS
    "CAT": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 5, 'slow': 13}},
    "UNP": {"strategy": "RSI Mean Reversion", "params": {'rsi_low': 30, 'rsi_high': 60}},
    "GE": {"strategy": "Golden Cross (Trend)", "params": {'fast': 50, 'slow': 200}},
    "LIN": {"strategy": "MACD Momentum", "params": {'fast': 12, 'slow': 26, 'signal': 9}},
    "NEE": {"strategy": "EMA 8/21 Crossover", "params": {'fast': 5, 'slow': 13}},
    "SHW": {"strategy": "Bollinger Breakout", "params": {'window': 20, 'std_dev': 2}}
}
