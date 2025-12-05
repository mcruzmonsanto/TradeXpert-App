# scanner.py
import yfinance as yf
import pandas as pd
import config as cfg  # ¡Asegúrate de haber actualizado config.py con 55 y 90!

def market_scanner():
    print(f"--- 📡 ESCÁNER DE MERCADO: {cfg.SYMBOL} ---")
    print("Conectando con la bolsa en tiempo real...")

    # 1. Descargamos datos "hasta el momento actual"
    # period='2y' descarga los últimos 2 años automáticamente hasta hoy
    df = yf.ticker.Ticker(cfg.SYMBOL).history(period="2y")
    
    if df.empty:
        print("❌ Error: No se pudieron obtener datos en tiempo real.")
        return

    # 2. Calculamos los indicadores con TUS PARÁMETROS ÓPTIMOS
    # Asegúrate de que en config.py tengas SMA_FAST=55 y SMA_SLOW=90
    df['SMA_Fast'] = df['Close'].rolling(window=cfg.SMA_FAST).mean()
    df['SMA_Slow'] = df['Close'].rolling(window=cfg.SMA_SLOW).mean()

    # Cálculo RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 3. ANÁLISIS DE LA ÚLTIMA VELA (El día de hoy)
    last_candle = df.iloc[-1]      # Datos de hoy
    prev_candle = df.iloc[-2]      # Datos de ayer (para comparar cruces)
    
    current_price = last_candle['Close']
    sma_fast_val = last_candle['SMA_Fast']
    sma_slow_val = last_candle['SMA_Slow']
    rsi_val = last_candle['RSI']

    print("-" * 40)
    print(f"📅 FECHA: {last_candle.name.strftime('%Y-%m-%d')}")
    print(f"💲 PRECIO ACTUAL: ${current_price:.2f}")
    print(f"📈 MEDIA RÁPIDA ({cfg.SMA_FAST}): {sma_fast_val:.2f}")
    print(f"📉 MEDIA LENTA  ({cfg.SMA_SLOW}): {sma_slow_val:.2f}")
    print(f"📊 RSI (Fuerza): {rsi_val:.2f}")
    print("-" * 40)

    # 4. EL CEREBRO DE DECISIÓN
    # Estado del Sistema
    trend = "ALCISTA (Bullish)" if sma_fast_val > sma_slow_val else "BAJISTA (Bearish)"
    
    print(f"ESTADO TÉCNICO: Tendencia {trend}")
    
    # Señales
    # ¿Hubo cruce hoy? (Ayer la rápida estaba abajo, hoy está arriba)
    golden_cross = (prev_candle['SMA_Fast'] < prev_candle['SMA_Slow']) and (sma_fast_val > sma_slow_val)
    death_cross = (prev_candle['SMA_Fast'] > prev_candle['SMA_Slow']) and (sma_fast_val < sma_slow_val)

    print("\n📢 --- CONCLUSIÓN DEL MENTOR ---")
    
    if golden_cross and rsi_val < cfg.RSI_THRESHOLD:
        print("🟢 SEÑAL DE ENTRADA DETECTADA: ¡COMPRAR! 🟢")
        print("Motivo: Cruce Dorado confirmado y RSI saludable.")
        
    elif death_cross:
        print("🔴 SEÑAL DE SALIDA DETECTADA: ¡VENDER! 🔴")
        print("Motivo: Cruce de la Muerte. Protege tu capital.")
        
    elif sma_fast_val > sma_slow_val:
        if rsi_val > 70:
            print("⚠️ PRECAUCIÓN: Tendencia Alcista pero RSI Sobrecomprado.")
            print("Acción: MANTENER (Hold), pero ajusta tus Stop Loss. No compres más.")
        else:
            print("🔵 ESTADO: MANTENER (Hold).")
            print("La tendencia sigue siendo tu amiga. Deja correr las ganancias.")
            
    else:
        print("⚪ ESTADO: ESPERAR (Cash).")
        print("El mercado es bajista. Tu dinero está mejor en tu bolsillo.")

if __name__ == "__main__":
    market_scanner()