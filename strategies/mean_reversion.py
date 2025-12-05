# strategies/mean_reversion.py
import pandas as pd

def detect_bounce_play(df, rsi_limit):
    """
    Estrategia 2: Reversión a la Media.
    Detecta si una acción ha caído demasiado (Pánico) y es probable un rebote.
    """
    if df is None or df.empty:
        return {"signal": "NEUTRO", "color": "gray", "reason": "Sin datos"}

    # Obtenemos el último dato disponible
    today = df.iloc[-1]
    
    rsi = today['RSI']
    
    # LÓGICA DE DECISIÓN
    # 1. Compra por Pánico (Oportunidad)
    if rsi < rsi_limit:
        return {
            "signal": "¡OPORTUNIDAD DE REBOTE! 💎", 
            "color": "green", 
            "reason": f"Sobreventa Extrema (RSI {rsi:.2f})"
        }
    
    # 2. Venta por Recuperación (Ya subió lo suficiente)
    elif rsi > 50:
        return {
            "signal": "VENDER REBOTE / NEUTRO", 
            "color": "red", 
            "reason": "El precio ya recuperó su media"
        }
        
    # 3. Tierra de nadie
    else:
        return {
            "signal": "ESPERAR", 
            "color": "gray", 
            "reason": "Sin condiciones extremas"
        }