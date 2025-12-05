# classes/scout.py
import yfinance as yf
import pandas as pd
# IMPORTAMOS LAS 4 ESTRATEGIAS
from classes.strategies import (
    GoldenCrossStrategy, 
    MeanReversionStrategy, 
    BollingerBreakoutStrategy, 
    MACDStrategy
)

class AssetScout:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = self._download_data()
        # Cargamos el arsenal completo
        self.strategies = [
            GoldenCrossStrategy(), 
            MeanReversionStrategy(),
            BollingerBreakoutStrategy(),
            MACDStrategy()
        ]

    def _download_data(self):
        # Usamos try/except para evitar errores si un ticker falla
        try:
            df = yf.Ticker(self.ticker).history(period="5y")
            return df
        except:
            return pd.DataFrame()

    def optimize(self):
        if self.data.empty: return None
        
        global_best_return = -999
        global_best_strat = None
        global_best_params = None

        # --- 1. GOLDEN CROSS ---
        strat = self.strategies[0]
        for fast in [20, 50]:
            for slow in [100, 200]:
                if fast >= slow: continue
                params = {'fast': fast, 'slow': slow}
                ret = strat.backtest(self.data, params)
                if ret > global_best_return:
                    global_best_return = ret
                    global_best_strat = strat.name
                    global_best_params = params

        # --- 2. MEAN REVERSION ---
        strat = self.strategies[1]
        for low in [25, 30, 35]:
            for high in [60, 70, 80]:
                params = {'rsi_low': low, 'rsi_high': high}
                ret = strat.backtest(self.data, params)
                if ret > global_best_return:
                    global_best_return = ret
                    global_best_strat = strat.name
                    global_best_params = params

        # --- 3. BOLLINGER BREAKOUT ---
        strat = self.strategies[2]
        for window in [20, 30]:
            for std in [2, 2.5]: # 2 es estándar, 2.5 exige movimientos más fuertes
                params = {'window': window, 'std_dev': std}
                ret = strat.backtest(self.data, params)
                if ret > global_best_return:
                    global_best_return = ret
                    global_best_strat = strat.name
                    global_best_params = params

        # --- 4. MACD MOMENTUM ---
        strat = self.strategies[3]
        # MACD Estándar (12,26,9) vs Rápido (8,21,5)
        configs = [{'fast': 12, 'slow': 26, 'signal': 9}, {'fast': 8, 'slow': 21, 'signal': 5}]
        for params in configs:
            ret = strat.backtest(self.data, params)
            if ret > global_best_return:
                global_best_return = ret
                global_best_strat = strat.name
                global_best_params = params

        return {
            "Ticker": self.ticker,
            "Estrategia Ganadora": global_best_strat,
            "Retorno 5y": f"{global_best_return*100:.2f}%",
            "Mejores Parametros": global_best_params
        }