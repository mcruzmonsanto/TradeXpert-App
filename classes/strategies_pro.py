import pandas as pd
import numpy as np
from classes.strategies import BaseStrategy

# --- 1. SUPERTREND STRATEGY ---
class SuperTrendStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("SuperTrend Pro")

    def generate_signals(self, df, params):
        period = params.get('period', 10)
        multiplier = params.get('multiplier', 3.0)
        
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        hl2 = (high + low) / 2
        basic_upper = hl2 + (multiplier * atr)
        basic_lower = hl2 - (multiplier * atr)
        
        final_upper = np.zeros(len(df))
        final_lower = np.zeros(len(df))
        supertrend = np.zeros(len(df))
        trend = np.zeros(len(df)) 
        
        close_vals = close.values
        bu = basic_upper.values
        bl = basic_lower.values
        
        for i in range(1, len(df)):
            if bu[i] < final_upper[i-1] or close_vals[i-1] > final_upper[i-1]:
                final_upper[i] = bu[i]
            else:
                final_upper[i] = final_upper[i-1]
                
            if bl[i] > final_lower[i-1] or close_vals[i-1] < final_lower[i-1]:
                final_lower[i] = bl[i]
            else:
                final_lower[i] = final_lower[i-1]
                
            prev_trend = trend[i-1] if i > 0 else 1
            
            if prev_trend == 1:
                if close_vals[i] < final_lower[i]:
                    trend[i] = -1
                    supertrend[i] = final_upper[i]
                else:
                    trend[i] = 1
                    supertrend[i] = final_lower[i]
            else:
                if close_vals[i] > final_upper[i]:
                    trend[i] = 1
                    supertrend[i] = final_lower[i]
                else:
                    trend[i] = -1
                    supertrend[i] = final_upper[i]
                    
        df['SuperTrend'] = supertrend
        df['Trend_Dir'] = trend
        df['Signal'] = np.where(df['Trend_Dir'] == 1, 1, 0)
        return df

# --- 2. SQUEEZE MOMENTUM ---
class SqueezeMomentumStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Squeeze Momentum")

    def generate_signals(self, df, params):
        bb_len = params.get('bb_len', 20)
        bb_mult = params.get('bb_mult', 2.0)
        kc_len = params.get('kc_len', 20)
        kc_mult = params.get('kc_mult', 1.5)
        
        mean = df['Close'].rolling(bb_len).mean()
        std = df['Close'].rolling(bb_len).std()
        bb_upper = mean + (std * bb_mult)
        bb_lower = mean - (std * bb_mult)
        
        high, low, close = df['High'], df['Low'], df['Close']
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(kc_len).mean()
        
        kc_upper = mean + (atr * kc_mult)
        kc_lower = mean - (atr * kc_mult)
        
        # Momentum simplificado
        val = close - ((df['High'] + df['Low']) / 2).rolling(bb_len).mean()
        df['Momentum'] = val.ewm(span=bb_len, adjust=False).mean()
        
        momentum_positivo = df['Momentum'] > 0
        df['Signal'] = np.where(momentum_positivo, 1, 0)
        return df

# --- 3. ADX STRATEGY ---
class ADXStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("ADX & DI Trend")

    def generate_signals(self, df, params):
        period = params.get('period', 14)
        threshold = params.get('adx_threshold', 25)
        
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = minus_dm.abs()
        
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/period).mean() / atr)
        
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        df['ADX'] = dx.ewm(alpha=1/period).mean()
        
        trend_strong = df['ADX'] > threshold
        trend_bullish = plus_di > minus_di
        
        df['Signal'] = np.where(trend_strong & trend_bullish, 1, 0)
        return df
