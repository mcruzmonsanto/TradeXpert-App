import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

# --- CLASE PADRE (BASE) ---
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
        if df.empty: 
            return {"return": -np.inf, "sharpe": 0, "drawdown": 0}
        
        data = df.copy()
        data = self.generate_signals(data, params)
        
        # Cálculos de Retorno
        data['Market_Return'] = data['Close'].pct_change()
        data['Strategy_Return'] = data['Market_Return'] * data['Signal'].shift(1)
        
        # 1. Retorno Total Acumulado
        equity_curve = (1 + data['Strategy_Return']).cumprod()
        if equity_curve.empty:
             return {"return": -np.inf, "sharpe": 0, "drawdown": 0}

        total_return = equity_curve.iloc[-1] - 1
        
        # 2. Max Drawdown
        peak = equity_curve.cummax()
        drawdown = (equity_curve - peak) / peak
        max_drawdown = drawdown.min()
        
        # 3. Sharpe Ratio
        mean_return = data['Strategy_Return'].mean()
        std_return = data['Strategy_Return'].std()
        
        if std_return == 0 or np.isnan(std_return):
            sharpe = 0
        else:
            sharpe = (mean_return / std_return) * (252 ** 0.5)
            
        return {
            "return": total_return,
            "sharpe": sharpe,
            "drawdown": max_drawdown,
            "equity_curve": equity_curve
        }

# --- ESTRATEGIA 1: GOLDEN CROSS (TENDENCIA) ---
class GoldenCrossStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Golden Cross (Trend)")

    def generate_signals(self, df, params):
        fast = params.get('fast', 50)
        slow = params.get('slow', 200)
        
        df['SMA_Fast'] = df['Close'].rolling(window=fast).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=slow).mean()
        
        df['Signal'] = np.where(df['SMA_Fast'] > df['SMA_Slow'], 1, 0)
        return df

# --- ESTRATEGIA 2: MEAN REVERSION (REBOTE RSI) ---
class MeanReversionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("RSI Mean Reversion")

    def generate_signals(self, df, params):
        rsi_low = params.get('rsi_low', 30)
        rsi_high = params.get('rsi_high', 70)
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
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

# --- ESTRATEGIA 3: BOLLINGER BREAKOUT ---
class BollingerBreakoutStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Bollinger Breakout")

    def generate_signals(self, df, params):
        window = params.get('window', 20)
        std_dev = params.get('std_dev', 2)
        
        df['BB_Mid'] = df['Close'].rolling(window=window).mean()
        std = df['Close'].rolling(window=window).std()
        df['BB_Upper'] = df['BB_Mid'] + (std * std_dev)
        
        signals = np.zeros(len(df))
        position = 0
        close = df['Close'].values
        upper = df['BB_Upper'].values
        mid = df['BB_Mid'].values
        
        for i in range(len(df)):
            if pd.isna(upper[i]): continue
            if position == 0 and close[i] > upper[i]:
                position = 1
            elif position == 1 and close[i] < mid[i]:
                position = 0
            signals[i] = position
            
        df['Signal'] = signals
        return df

# --- ESTRATEGIA 4: MACD MOMENTUM ---
class MACDStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("MACD Momentum")

    def generate_signals(self, df, params):
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        sig = params.get('signal', 9)
        
        exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=sig, adjust=False).mean()
        
        df['Signal'] = np.where(df['MACD'] > df['Signal_Line'], 1, 0)
        return df

# --- ESTRATEGIA 5: EMA 8/21 (MOMENTUM RÁPIDO) ---
class EMAStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("EMA 8/21 Crossover")

    def generate_signals(self, df, params):
        fast = params.get('fast', 8)
        slow = params.get('slow', 21)
        
        df['EMA_Fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
        
        df['Signal'] = np.where(df['EMA_Fast'] > df['EMA_Slow'], 1, 0)
        return df

# --- ESTRATEGIA 6: STOCHASTIC RSI (FRANCOTIRADOR) ---
class StochRSIStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Stochastic RSI")

    def generate_signals(self, df, params):
        rsi_period = params.get('rsi_period', 14)
        stoch_period = params.get('stoch_period', 14)
        k_period = params.get('k_period', 3)
        d_period = params.get('d_period', 3)
        
        # 1. RSI Base
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
        rs = gain / loss
        df['RSI_Base'] = 100 - (100 / (1 + rs))
        
        # 2. StochRSI
        min_rsi = df['RSI_Base'].rolling(stoch_period).min()
        max_rsi = df['RSI_Base'].rolling(stoch_period).max()
        df['StochRSI'] = (df['RSI_Base'] - min_rsi) / (max_rsi - min_rsi)
        
        # 3. K y D
        df['Stoch_K'] = df['StochRSI'].rolling(k_period).mean() * 100
        df['Stoch_D'] = df['Stoch_K'].rolling(d_period).mean()
        
        # Señal: K > D (Tendencia alcista momentum)
        df['Signal'] = np.where(df['Stoch_K'] > df['Stoch_D'], 1, 0)
        return df

# --- ESTRATEGIA 7: AWESOME OSCILLATOR ---
class AwesomeOscillatorStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Awesome Oscillator")

    def generate_signals(self, df, params):
        fast = params.get('fast', 5)
        slow = params.get('slow', 34)
        
        median_price = (df['High'] + df['Low']) / 2
        ao_fast = median_price.rolling(window=fast).mean()
        ao_slow = median_price.rolling(window=slow).mean()
        df['AO'] = ao_fast - ao_slow
        
        # Señal: AO positivo (Zero Line Cross)
        df['Signal'] = np.where(df['AO'] > 0, 1, 0)
        return df
