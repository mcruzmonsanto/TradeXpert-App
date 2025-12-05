# classes/scout.py
import yfinance as yf
import pandas as pd
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy

class AssetScout:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = self._download_data()
        self.strategies = [GoldenCrossStrategy(), MeanReversionStrategy()]
        self.best_result = None

    def _download_data(self):
        """Descarga datos una sola vez"""
        print(f"📥 Descargando datos para {self.ticker}...")
        df = yf.Ticker(self.ticker).history(period="5y")
        return df

    def optimize(self):
        if self.data.empty: return None

        print(f"🔎 Iniciando Scouting para {self.ticker}...")
        
        global_best_return = -999
        global_best_strat = None
        global_best_params = None

        # --- FASE 1: OPTIMIZAR GOLDEN CROSS ---
        strat_gc = self.strategies[0]
        # Probamos combinaciones rápidas
        for fast in range(10, 60, 10):      # 10, 20, 30, 40, 50
            for slow in range(60, 200, 20): # 60, 80...
                if fast >= slow: continue
                
                params = {'fast': fast, 'slow': slow}
                ret = strat_gc.backtest(self.data, params)
                
                if ret > global_best_return:
                    global_best_return = ret
                    global_best_strat = strat_gc.name
                    global_best_params = params

        # --- FASE 2: OPTIMIZAR MEAN REVERSION ---
        strat_mr = self.strategies[1]
        # Probamos límites de RSI
        for low in [20, 25, 30, 35]:
            for high in [50, 60, 70, 80]:
                params = {'rsi_low': low, 'rsi_high': high}
                ret = strat_mr.backtest(self.data, params)
                
                if ret > global_best_return:
                    global_best_return = ret
                    global_best_strat = strat_mr.name
                    global_best_params = params

        # GUARDAMOS EL GANADOR
        self.best_result = {
            "Ticker": self.ticker,
            "Estrategia Ganadora": global_best_strat,
            "Retorno 5y": f"{global_best_return*100:.2f}%",
            "Mejores Parametros": global_best_params
        }
        
        return self.best_result