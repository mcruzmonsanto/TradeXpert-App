# classes/strategies.py
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

# --- CLASE PADRE (PLANTILLA) ---
class BaseStrategy(ABC):
    def __init__(self, name):
        self.name = name
        self.best_params = {}
        self.best_performance = -np.inf

    @abstractmethod
    def generate_signals(self, df, params):
        """Método que cada estrategia debe implementar a su manera"""
        pass

    def backtest(self, df, params):
        """Motor de Backtest universal para cualquier estrategia"""
        if df.empty: return -np.inf
        
        # Copia para no alterar original
        data = df.copy()
        
        # 1. Generar Señales (Polimorfismo: llama a la versión de la hija)
        data = self.generate_signals(data, params)
        
        # 2. Calcular Retornos
        data['Market_Return'] = data['Close'].pct_change()
        data['Strategy_Return'] = data['Market_Return'] * data['Signal'].shift(1)
        
        # 3. Calcular Rendimiento Acumulado
        total_return = (1 + data['Strategy_Return']).cumprod().iloc[-1] - 1
        return total_return

# --- ESTRATEGIA 1: GOLDEN CROSS (TENDENCIA) ---
class GoldenCrossStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Golden Cross (Trend)")

    def generate_signals(self, df, params):
        """Espera params: {'fast': int, 'slow': int}"""
        fast = params.get('fast', 50)
        slow = params.get('slow', 200)
        
        df['SMA_Fast'] = df['Close'].rolling(window=fast).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=slow).mean()
        
        df['Signal'] = 0
        # Condición: Rápida > Lenta
        df.loc[df['SMA_Fast'] > df['SMA_Slow'], 'Signal'] = 1
        return df

# --- ESTRATEGIA 2: MEAN REVERSION (REBOTE) ---
class MeanReversionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("RSI Mean Reversion")

    def generate_signals(self, df, params):
        """Espera params: {'rsi_low': int, 'rsi_high': int}"""
        rsi_low = params.get('rsi_low', 30)
        rsi_high = params.get('rsi_high', 70)
        
        # Cálculo RSI Manual
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        df['Signal'] = 0
        
        # Lógica de Estado (Requiere iteración o vectorización compleja)
        # Simplificación vectorizada: 
        # 1. Señal de entrada (1) cuando RSI < low
        # 2. Señal de salida (0) cuando RSI > high
        # Usamos ffill() para mantener la posición entre entrada y salida
        
        signals = np.zeros(len(df))
        position = 0
        
        rsi_values = df['RSI'].values
        
        for i in range(len(df)):
            if position == 0 and rsi_values[i] < rsi_low:
                position = 1
            elif position == 1 and rsi_values[i] > rsi_high:
                position = 0
            signals[i] = position
            
        df['Signal'] = signals
        return df