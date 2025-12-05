# strategies/golden_cross.py
import pandas as pd

def apply_strategy(df, fast_period, slow_period, rsi_limit):
    """
    Recibe un DataFrame con datos y devuelve el DataFrame con Señales
    """
    # 1. Calcular indicadores
    df['SMA_Fast'] = df['Close'].rolling(window=fast_period).mean()
    df['SMA_Slow'] = df['Close'].rolling(window=slow_period).mean()
    
    # RSI Simplificado
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 2. Lógica de Señal
    df['Signal'] = 0
    
    # Condición Larga (Compra)
    condition = (df['SMA_Fast'] > df['SMA_Slow']) & (df['RSI'] < rsi_limit)
    
    df.loc[condition, 'Signal'] = 1
    
    return df