# portfolio_manager.py
import yfinance as yf
import pandas as pd
import config as cfg
import time
from telegram_bot import send_msg  # Importamos nuestro bot

def analyze_ticker(symbol):
    """Analiza un solo activo y devuelve su estado y señal"""
    try:
        # Descargamos datos recientes (2 años es suficiente para medias de 90)
        df = yf.ticker.Ticker(symbol).history(period="2y")
        
        if df.empty: return None

        # CORRECCIÓN YFINANCE (Igual que en risk_backtest)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Cálculos Técnicos
        df['SMA_Fast'] = df['Close'].rolling(window=cfg.SMA_FAST).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=cfg.SMA_SLOW).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Datos de Hoy y Ayer
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        # Variables limpias
        price = float(today['Close'])
        sma_fast_today = float(today['SMA_Fast'])
        sma_slow_today = float(today['SMA_Slow'])
        
        sma_fast_yesterday = float(yesterday['SMA_Fast'])
        sma_slow_yesterday = float(yesterday['SMA_Slow'])
        
        rsi_val = float(today['RSI'])

        # Lógica de Señales
        trend = "ALCISTA" if sma_fast_today > sma_slow_today else "BAJISTA"
        
        # Detectar Cruces
        golden_cross = (sma_fast_yesterday < sma_slow_yesterday) and (sma_fast_today > sma_slow_today)
        death_cross = (sma_fast_yesterday > sma_slow_yesterday) and (sma_fast_today < sma_slow_today)
        
        # Determinar Acción Recomendada
        action = "ESPERAR"
        reason = "Sin señal clara"
        color = "⚪" # Blanco/Gris

        if trend == "BAJISTA":
            action = "ESPERAR / CASH"
            reason = "Tendencia Bajista"
            color = "🔴"
            
        elif trend == "ALCISTA":
            if golden_cross and rsi_val < cfg.RSI_THRESHOLD:
                action = "¡COMPRAR! (ENTRADA)"
                reason = "Cruce Dorado Confirmado"
                color = "🟢"
            elif rsi_val > 70:
                action = "MANTENER (CUIDADO)"
                reason = "Sobrecomprado (RSI Alto)"
                color = "⚠️"
            else:
                action = "MANTENER"
                reason = "Tendencia Saludable"
                color = "🔵"
        
        if death_cross:
            action = "¡VENDER! (SALIDA)"
            reason = "Cruce de la Muerte"
            color = "🔻"

        return {
            "Ticker": symbol,
            "Precio": price,
            "Tendencia": trend,
            "RSI": round(rsi_val, 2),
            "Acción": action,
            "Motivo": reason,
            "Icono": color
        }

    except Exception as e:
        print(f"Error analizando {symbol}: {e}")
        return None

def run_portfolio():
    print(f"\n--- 💼 GESTOR DE PORTAFOLIO MULTI-ACTIVO ---")
    
    report = []
    
    # Análisis
    print("Analizando mercado...", end=" ")
    for ticker in cfg.TICKERS:
        print(f"{ticker}...", end=" ", flush=True)
        # Llamamos a la función directamente (ya está en memoria)
        data = analyze_ticker(ticker) 
        if data:
            report.append(data)
        time.sleep(0.5)
        
    print("\nGenerando reporte...")
    
    # Construcción del Mensaje Telegram
    telegram_message = f"📊 **REPORTE DIARIO: {time.strftime('%Y-%m-%d')}**\n\n"
    hay_oportunidad = False
    
    for item in report:
        linea = f"{item['Icono']} *{item['Ticker']}*: ${item['Precio']:.2f}\n➡️ {item['Acción']}\n\n"
        telegram_message += linea
        if "COMPRAR" in item['Acción']:
            hay_oportunidad = True
    
    telegram_message += "-------------------\n"
    
    if hay_oportunidad:
        telegram_message += "🚀 **¡ALERTA! Señales de entrada.**"
    else:
        telegram_message += "😴 Sin novedades."

    # ENVIAR AL CELULAR
    print("Enviando reporte a tu móvil...")
    send_msg(telegram_message)
    
    # Guardar CSV
    df_report = pd.DataFrame(report)
    df_report.to_csv("data/Diario_Inversion.csv", index=False)
    print(f"✅ Proceso terminado.")

if __name__ == "__main__":
    # SOLUCIÓN: Simplemente llamamos a la función principal
    run_portfolio()