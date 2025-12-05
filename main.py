# main.py
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import os  # Necesario para manejar rutas de carpetas
import config as cfg
from strategies.golden_cross import apply_strategy

def save_signals(df):
    """Guarda los datos procesados en la carpeta data"""
    # Crear carpeta data si no existe
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Nombre del archivo dinámico
    filename = f"data/{cfg.SYMBOL}_signals.csv"
    
    # Guardamos solo las columnas importantes
    columns_to_save = ['Open', 'High', 'Low', 'Close', 'SMA_Fast', 'SMA_Slow', 'RSI', 'Signal']
    df[columns_to_save].to_csv(filename)
    print(f"✅ Bitácora guardada exitosamente en: {filename}")

def run_bot():
    print(f"--- Iniciando TradeXpert Bot para {cfg.SYMBOL} ---")
    
    # 1. Obtener Datos
    print("Descargando datos...")
    df = yf.download(cfg.SYMBOL, start=cfg.START_DATE, end=cfg.END_DATE)
    
    if df.empty:
        print("❌ Error: No se descargaron datos. Revisa tu conexión o el símbolo.")
        return

    # Limpieza de datos
    df.dropna(inplace=True)
    
    # 2. Aplicar Estrategia
    print("Analizando mercado...")
    df = apply_strategy(df, cfg.SMA_FAST, cfg.SMA_SLOW, cfg.RSI_THRESHOLD)
    
    # 3. GUARDAR RESULTADOS (NUEVO PASO)
    save_signals(df)
    
    # 4. Mostrar últimos registros en consola
    print("\n--- Últimas 5 velas analizadas ---")
    print(df[['Close', 'SMA_Fast', 'SMA_Slow', 'Signal']].tail())
    
    # 5. Graficar
    plt.figure(figsize=(12,6))
    plt.plot(df['Close'], label='Precio', alpha=0.5)
    plt.plot(df['SMA_Fast'], label=f'Rápida ({cfg.SMA_FAST})', color='orange')
    plt.plot(df['SMA_Slow'], label=f'Lenta ({cfg.SMA_SLOW})', color='green')
    
    # Marcar señales de compra en el gráfico
    # Buscamos donde la señal sea 1
    buy_signals = df[df['Signal'] == 1]
    if not buy_signals.empty:
        plt.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', label='Señal Compra', alpha=0.3)

    plt.title(f'Estrategia Golden Cross: {cfg.SYMBOL}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

if __name__ == "__main__":
    run_bot()