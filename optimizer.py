# optimizer.py
import yfinance as yf
import pandas as pd
import config as cfg

def optimize():
    print(f"--- Iniciando Optimización Genética para {cfg.SYMBOL} ---")
    
    # 1. Descargar datos una sola vez (Eficiencia)
    df_raw = yf.download(cfg.SYMBOL, start=cfg.START_DATE, end=cfg.END_DATE)
    df_raw.dropna(inplace=True)
    
    best_return = -999
    best_fast = 0
    best_slow = 0
    
    # 2. BUCLE DE FUERZA BRUTA INTELIGENTE
    # Probaremos medias rápidas de 10 a 60
    for fast in range(10, 60, 5):
        # Probaremos medias lentas de 60 a 200
        for slow in range(60, 210, 10):
            
            if fast >= slow: continue # La rápida siempre debe ser menor
            
            # Copia limpia para no ensuciar datos
            df = df_raw.copy()
            
            # Lógica Rápida (Sin gráficos ni prints para velocidad)
            df['SMA_Fast'] = df['Close'].rolling(window=fast).mean()
            df['SMA_Slow'] = df['Close'].rolling(window=slow).mean()
            df['Signal'] = 0
            # Solo lógica de cruce simple para testear rápido
            condition = (df['SMA_Fast'] > df['SMA_Slow'])
            df.loc[condition, 'Signal'] = 1
            
            # Calcular retorno acumulado
            df['Market_Return'] = df['Close'].pct_change()
            df['Strategy_Return'] = df['Market_Return'] * df['Signal'].shift(1)
            total_return = (1 + df['Strategy_Return']).cumprod().iloc[-1] - 1
            
            # ¿Es este el nuevo récord?
            if total_return > best_return:
                best_return = total_return
                best_fast = fast
                best_slow = slow
                print(f"🚀 Nuevo Récord: SMA {fast}/{slow} -> Retorno: {total_return*100:.2f}%")

    print("-" * 40)
    print("🏆 MEJOR COMBINACIÓN ENCONTRADA 🏆")
    print(f"Media Rápida: {best_fast}")
    print(f"Media Lenta:  {best_slow}")
    print(f"Retorno Potencial: {best_return*100:.2f}%")
    print("-" * 40)
    print("Tip: Ahora ve a config.py y actualiza tus valores con estos nuevos números.")

if __name__ == "__main__":
    optimize()