# classes/strategies.py
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

# --- CLASE PADRE MEJORADA ---
class BaseStrategy(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def generate_signals(self, df, params):
        pass

    def backtest(self, df, params):
        """
        Retorna un DICCIONARIO completo con métricas de riesgo.
        """
        if df.empty: return {"return": -np.inf, "sharpe": 0, "drawdown": 0}
        
        data = df.copy()
        data = self.generate_signals(data, params)
        
        # Cálculos de Retorno
        data['Market_Return'] = data['Close'].pct_change()
        data['Strategy_Return'] = data['Market_Return'] * data['Signal'].shift(1)
        
        # 1. Retorno Total Acumulado
        equity_curve = (1 + data['Strategy_Return']).cumprod()
        total_return = equity_curve.iloc[-1] - 1
        
        # 2. Max Drawdown (El dolor máximo)
        peak = equity_curve.cummax()
        drawdown = (equity_curve - peak) / peak
        max_drawdown = drawdown.min() # Será un número negativo (ej: -0.30)
        
        # 3. Sharpe Ratio (Rentabilidad ajustada al riesgo)
        # Asumimos 252 días de trading al año. Risk Free Rate = 0 simplificado.
        mean_return = data['Strategy_Return'].mean()
        std_return = data['Strategy_Return'].std()
        
        if std_return == 0:
            sharpe = 0
        else:
            sharpe = (mean_return / std_return) * (252 ** 0.5)
            
        return {
            "return": total_return,
            "sharpe": sharpe,
            "drawdown": max_drawdown,
            "equity_curve": equity_curve # Guardamos la curva por si queremos graficarla
        }

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

# --- ESTRATEGIA 3: BOLLINGER BREAKOUT (VOLATILIDAD) ---
class BollingerBreakoutStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Bollinger Breakout")

    def generate_signals(self, df, params):
        """params: {'window': 20, 'std_dev': 2}"""
        window = params.get('window', 20)
        std_dev = params.get('std_dev', 2)
        
        # Cálculo de Bandas
        df['BB_Mid'] = df['Close'].rolling(window=window).mean()
        std = df['Close'].rolling(window=window).std()
        df['BB_Upper'] = df['BB_Mid'] + (std * std_dev)
        df['BB_Lower'] = df['BB_Mid'] - (std * std_dev)
        
        df['Signal'] = 0
        
        # Lógica de Ruptura:
        # COMPRA: Precio cierra por ENCIMA de la banda superior (Explosión)
        # VENTA: Precio vuelve a tocar la media central (Reversión a la media)
        
        signals = np.zeros(len(df))
        position = 0
        
        close = df['Close'].values
        upper = df['BB_Upper'].values
        mid = df['BB_Mid'].values
        
        for i in range(len(df)):
            if pd.isna(upper[i]): continue
            
            # Entrada: Rompe techo
            if position == 0 and close[i] > upper[i]:
                position = 1
            # Salida: Toca el centro (Stop dinámico)
            elif position == 1 and close[i] < mid[i]:
                position = 0
            
            signals[i] = position
            
        df['Signal'] = signals
        return df

# --- ESTRATEGIA 4: MACD MOMENTUM (IMPULSO) ---
class MACDStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("MACD Momentum")

    def generate_signals(self, df, params):
        """params: {'fast': 12, 'slow': 26, 'signal': 9}"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        sig = params.get('signal', 9)
        
        # Cálculo MACD
        exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=sig, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal_Line']
        
        df['Signal'] = 0
        
        # Lógica: Cruce de MACD sobre Señal
        # Vectorizado para velocidad
        cruce_compra = (df['MACD'] > df['Signal_Line'])
        
        # Mantenemos posición mientras MACD esté arriba
        df.loc[cruce_compra, 'Signal'] = 1
        return df