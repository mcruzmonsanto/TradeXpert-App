# risk_backtest.py
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import config as cfg

# --- CONFIGURACIÓN DE RIESGO ---
STOP_LOSS_PCT = 0.10  # 10% de margen de caída permitido

def run_risk_backtest():
    print(f"--- 🛡️ SIMULACIÓN CON GESTIÓN DE RIESGO (Trailing Stop) ---")
    print(f"Activo: {cfg.SYMBOL} | Stop Loss Dinámico: {STOP_LOSS_PCT*100}%")

    # 1. Preparar Datos
    df = yf.download(cfg.SYMBOL, start=cfg.START_DATE, end=cfg.END_DATE)
    
    # CORRECCIÓN PARA YFINANCE RECIENTE:
    # A veces yfinance devuelve MultiIndex, esto asegura que solo tengamos una capa de columnas
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df.dropna(inplace=True)
    
    # Calcular indicadores
    df['SMA_Fast'] = df['Close'].rolling(window=cfg.SMA_FAST).mean()
    df['SMA_Slow'] = df['Close'].rolling(window=cfg.SMA_SLOW).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 2. BUCLE DE SIMULACIÓN (DÍA A DÍA)
    capital = float(cfg.INITIAL_CAPITAL) # Aseguramos que sea float
    position = 0.0       
    highest_price = 0.0  
    stop_price = 0.0     
    
    equity_curve = []  
    
    # Recorremos el DataFrame fila por fila
    for i in range(len(df)):
        # Necesitamos datos suficientes para las medias
        if i < cfg.SMA_SLOW:
            equity_curve.append(capital)
            continue
            
        current_date = df.index[i]
        
        # --- CORRECCIÓN CRÍTICA AQUÍ ---
        # Usamos float() para asegurar que obtenemos un número, no una Serie
        price = float(df['Close'].iloc[i])
        sma_fast = float(df['SMA_Fast'].iloc[i])
        sma_slow = float(df['SMA_Slow'].iloc[i])
        rsi = float(df['RSI'].iloc[i])
        
        # Valor actual de la cartera
        if position > 0:
            current_equity = capital + (position * price)
        else:
            current_equity = capital
            
        equity_curve.append(current_equity)

        # --- LÓGICA DE TRADING ---
        
        # SI NO TENEMOS ACCIONES (Buscamos Comprar)
        if position == 0:
            if sma_fast > sma_slow and rsi < cfg.RSI_THRESHOLD:
                position = capital / price 
                capital = 0.0 
                highest_price = price 
                stop_price = price * (1 - STOP_LOSS_PCT) 

        # SI TENEMOS ACCIONES (Gestionamos la posición)
        elif position > 0:
            # 1. ACTUALIZAR TRAILING STOP
            if price > highest_price:
                highest_price = price
                new_stop = highest_price * (1 - STOP_LOSS_PCT)
                if new_stop > stop_price:
                    stop_price = new_stop
            
            # 2. VERIFICAR SI TOCÓ EL STOP LOSS
            if price < stop_price:
                capital = position * price
                position = 0.0
            
            # 3. VERIFICAR SALIDA TÉCNICA
            elif sma_fast < sma_slow:
                capital = position * price
                position = 0.0

    # 3. RESULTADOS FINALES
    # Si al final nos quedamos con acciones, las vendemos al precio final para calcular el total
    if position > 0:
        final_equity = position * float(df['Close'].iloc[-1])
    else:
        final_equity = equity_curve[-1]

    # Convertir curva a DataFrame para análisis
    df_result = pd.DataFrame(equity_curve, index=df.index, columns=['Equity'])
    
    df_result['Peak'] = df_result['Equity'].cummax()
    df_result['Drawdown'] = (df_result['Equity'] - df_result['Peak']) / df_result['Peak']
    max_dd = df_result['Drawdown'].min() * 100

    print("-" * 40)
    print(f"RESULTADO MEJORADO ({cfg.START_DATE} - {cfg.END_DATE})")
    print("-" * 40)
    print(f"Capital Final:        ${final_equity:.2f}")
    print(f"Retorno Total:        {((final_equity/cfg.INITIAL_CAPITAL)-1)*100:.2f}%")
    print(f"Max Drawdown (Riesgo): {max_dd:.2f}%")
    print("-" * 40)
    
    plt.figure(figsize=(12, 6))
    plt.plot(df_result.index, df_result['Equity'], label='Con Trailing Stop (10%)', color='purple')
    plt.title(f'Impacto de la Gestión de Riesgo: {cfg.SYMBOL}')
    plt.ylabel('Capital (USD)')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run_risk_backtest()