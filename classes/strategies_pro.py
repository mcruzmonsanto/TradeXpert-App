import pandas as pd
import numpy as np
from classes.strategies import BaseStrategy # Heredamos la estructura base

# --- 1. SUPERTREND STRATEGY (El Rey de TradingView) ---
class SuperTrendStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("SuperTrend Pro")

    def generate_signals(self, df, params):
        """params: {'period': 10, 'multiplier': 3.0}"""
        period = params.get('period', 10)
        multiplier = params.get('multiplier', 3.0)
        
        # 1. Calcular ATR
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        # 2. Calcular Bandas Básicas
        hl2 = (high + low) / 2
        basic_upper = hl2 + (multiplier * atr)
        basic_lower = hl2 - (multiplier * atr)
        
        # 3. Calcular SuperTrend (Lógica Iterativa)
        # Necesitamos iterar porque el valor de hoy depende del de ayer
        final_upper = np.zeros(len(df))
        final_lower = np.zeros(len(df))
        supertrend = np.zeros(len(df))
        trend = np.zeros(len(df)) # 1 = Bullish, -1 = Bearish
        
        # Inicialización
        close_vals = close.values
        bu = basic_upper.values
        bl = basic_lower.values
        
        for i in range(1, len(df)):
            # Upper Band Logic
            if bu[i] < final_upper[i-1] or close_vals[i-1] > final_upper[i-1]:
                final_upper[i] = bu[i]
            else:
                final_upper[i] = final_upper[i-1]
                
            # Lower Band Logic
            if bl[i] > final_lower[i-1] or close_vals[i-1] < final_lower[i-1]:
                final_lower[i] = bl[i]
            else:
                final_lower[i] = final_lower[i-1]
                
            # Trend Logic
            # Si era Bullish (1) y cierra abajo del Lower -> Bearish (-1)
            # Si era Bearish (-1) y cierra arriba del Upper -> Bullish (1)
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
        
        # SEÑAL:
        # 1 = Estamos en Tendencia Alcista (Precio sobre la línea)
        # 0 = Estamos en Tendencia Bajista
        df['Signal'] = np.where(df['Trend_Dir'] == 1, 1, 0)
        
        return df

# --- 2. SQUEEZE MOMENTUM (Estilo LazyBear) ---
class SqueezeMomentumStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Squeeze Momentum (LazyBear)")

    def generate_signals(self, df, params):
        """params: {'bb_len': 20, 'bb_mult': 2.0, 'kc_len': 20, 'kc_mult': 1.5}"""
        bb_len = params.get('bb_len', 20)
        bb_mult = params.get('bb_mult', 2.0)
        kc_len = params.get('kc_len', 20)
        kc_mult = params.get('kc_mult', 1.5)
        
        # 1. Bollinger Bands
        mean = df['Close'].rolling(bb_len).mean()
        std = df['Close'].rolling(bb_len).std()
        bb_upper = mean + (std * bb_mult)
        bb_lower = mean - (std * bb_mult)
        
        # 2. Keltner Channels (Usan ATR)
        # TR calculation (reutilizamos o recalculamos rapido)
        high, low, close = df['High'], df['Low'], df['Close']
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(kc_len).mean()
        
        kc_upper = mean + (atr * kc_mult)
        kc_lower = mean - (atr * kc_mult)
        
        # 3. Detección de SQUEEZE (Energía acumulada)
        # Ocurre cuando las bandas de Bollinger se meten DENTRO de las de Keltner
        # Esto significa volatilidad extremadamente baja -> Explosión inminente
        df['Squeeze_On'] = (bb_lower > kc_lower) & (bb_upper < kc_upper)
        df['Squeeze_Off'] = (bb_lower < kc_lower) & (bb_upper > kc_upper)
        
        # 4. Momentum (Linear Regression del precio - promedio)
        # Simplificación para Python: Usaremos un oscilador suavizado similar
        # Value = Close - Average(High, Low)
        # Smoothed by LinReg (Simulado con EMA para velocidad)
        val = close - ((df['High'] + df['Low']) / 2).rolling(bb_len).mean()
        df['Momentum'] = val.ewm(span=bb_len, adjust=False).mean() # Aprox del script original
        
        df['Signal'] = 0
        
        # LÓGICA DE DISPARO:
        # Compramos cuando el Squeeze "se dispara" (Off) Y el momentum es positivo y creciente
        # O simplemente seguimos el Momentum si no hay squeeze
        
        momentum_positivo = df['Momentum'] > 0
        momentum_creciente = df['Momentum'] > df['Momentum'].shift(1)
        
        # Señal: Momentum Positivo
        df['Signal'] = np.where(momentum_positivo, 1, 0)
        
        return df

# --- 3. ADX TREND STRENGTH (Filtro Institucional) ---
class ADXStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("ADX & DI Trend")

    def generate_signals(self, df, params):
        """params: {'period': 14, 'adx_threshold': 25}"""
        period = params.get('period', 14)
        threshold = params.get('adx_threshold', 25)
        
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        # +DM y -DM
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0 # Ojo: minus_dm es negativo cuando baja
        minus_dm = minus_dm.abs()
        
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/period).mean() / atr)
        
        # ADX
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        df['ADX'] = dx.ewm(alpha=1/period).mean()
        
        df['Signal'] = 0
        
        # LÓGICA:
        # 1. ADX > Threshold (La tendencia es fuerte, vale la pena operar)
        # 2. +DI > -DI (La tendencia es Alcista)
        trend_strong = df['ADX'] > threshold
        trend_bullish = plus_di > minus_di
        
        df['Signal'] = np.where(trend_strong & trend_bullish, 1, 0)
        
        return df
