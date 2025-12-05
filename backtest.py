# backtest.py
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import config as cfg
from strategies.golden_cross import apply_strategy

def run_backtest():
    print(f"--- Iniciando Backtest Profesional para {cfg.SYMBOL} ---")
    print(f"Capital Inicial: ${cfg.INITIAL_CAPITAL}")

    # 1. Preparar Datos
    df = yf.download(cfg.SYMBOL, start=cfg.START_DATE, end=cfg.END_DATE)
    df.dropna(inplace=True)
    
    # 2. Aplicar la Estrategia (Recuperamos las señales)
    df = apply_strategy(df, cfg.SMA_FAST, cfg.SMA_SLOW, cfg.RSI_THRESHOLD)

    # 3. CÁLCULO DE RENDIMIENTOS (El Corazón Financiero)
    
    # Calculamos cuánto varió el precio porcentualmente día a día
    # Ejemplo: Si sube de 100 a 101, el retorno es 0.01 (1%)
    df['Market_Return'] = df['Close'].pct_change()

    # Calculamos el retorno de NUESTRA estrategia
    # Lógica: Multiplicamos el retorno del mercado por la señal de AYER.
    # Si ayer Signal fue 1, hoy asumimos el retorno del mercado.
    # Si ayer Signal fue 0, hoy no ganamos ni perdemos nada (0).
    df['Strategy_Return'] = df['Market_Return'] * df['Signal'].shift(1)

    # 4. CURVA DE CAPITAL (Equity Curve)
    # Simulamos el crecimiento de los $500
    df['Strategy_Equity'] = cfg.INITIAL_CAPITAL * (1 + df['Strategy_Return']).cumprod()
    
    # Calculamos también qué hubiera pasado si solo comprabas y esperabas (Buy & Hold)
    df['Buy_Hold_Equity'] = cfg.INITIAL_CAPITAL * (1 + df['Market_Return']).cumprod()

    # 5. CÁLCULO DE DRAWDOWN (Riesgo)
    # Calculamos el pico máximo histórico acumulado
    df['Peak'] = df['Strategy_Equity'].cummax()
    # Calculamos el porcentaje de caída desde ese pico
    df['Drawdown'] = (df['Strategy_Equity'] - df['Peak']) / df['Peak']
    max_drawdown = df['Drawdown'].min() * 100

    # 6. RESULTADOS FINALES
    final_equity = df['Strategy_Equity'].iloc[-1]
    profit = final_equity - cfg.INITIAL_CAPITAL
    buy_hold_final = df['Buy_Hold_Equity'].iloc[-1]

    print("-" * 40)
    print(f"RESULTADO FINAL ({cfg.START_DATE} - {cfg.END_DATE})")
    print("-" * 40)
    print(f"Capital Final Estrategia: ${final_equity:.2f}")
    print(f"Beneficio Neto:           ${profit:.2f}")
    print(f"Retorno Total:            {((final_equity/cfg.INITIAL_CAPITAL)-1)*100:.2f}%")
    print(f"Max Drawdown (Riesgo):    {max_drawdown:.2f}% (Máxima caída soportada)")
    print("-" * 40)
    print(f"vs. Buy & Hold (Simple):  ${buy_hold_final:.2f}")
    print("-" * 40)

    # 7. GRAFICAR LA COMPARATIVA
    plt.figure(figsize=(12, 8))
    
    # Gráfico Superior: Curva de Capital
    plt.subplot(2, 1, 1)
    plt.plot(df['Strategy_Equity'], label='Tu Robot (Estrategia)', color='green')
    plt.plot(df['Buy_Hold_Equity'], label='Buy & Hold (Mercado)', color='gray', linestyle='--')
    plt.title(f'Simulación de Rendimiento: {cfg.SYMBOL} (${cfg.INITIAL_CAPITAL} Inicial)')
    plt.ylabel('Capital (USD)')
    plt.legend()
    plt.grid(True)

    # Gráfico Inferior: Drawdown (Dolor)
    plt.subplot(2, 1, 2)
    plt.plot(df['Drawdown'], label='Drawdown (Caída desde pico)', color='red')
    plt.fill_between(df.index, df['Drawdown'], 0, color='red', alpha=0.3)
    plt.title('Perfil de Riesgo (Drawdown)')
    plt.ylabel('% Caída')
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_backtest()