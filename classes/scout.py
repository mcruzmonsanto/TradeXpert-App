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
        
        global_best_score = -999 # Usaremos un score combinado
        global_best_result = None

        # Función auxiliar para evaluar una iteración
        def evaluate_iteration(strat_obj, params):
            nonlocal global_best_score, global_best_result
            
            # Ejecutamos backtest (ahora devuelve diccionario)
            metrics = strat_obj.backtest(self.data, params)
            
            ret = metrics["return"]
            sharpe = metrics["sharpe"]
            dd = metrics["drawdown"]
            
            # --- CRITERIO DE SELECCIÓN ---
            # Aquí defines qué te importa más. 
            # Filtro: Si el Drawdown es peor que -50%, descartamos la estrategia (muy arriesgada)
            if dd < -0.50: 
                return

            # Score: Priorizamos Retorno, pero el Sharpe ayuda a desempatar calidad
            score = ret 
            
            if score > global_best_score:
                global_best_score = score
                global_best_result = {
                    "Ticker": self.ticker,
                    "Estrategia": strat_obj.name,
                    "Retorno": ret,
                    "Sharpe": sharpe,
                    "Drawdown": dd,
                    "Params": params
                }

        # --- BUCLES DE OPTIMIZACIÓN (Igual que antes pero llamando a evaluate) ---
        
        # 1. GOLDEN CROSS
        strat = self.strategies[0]
        for fast in [20, 50]:
            for slow in [100, 200]:
                if fast >= slow: continue
                evaluate_iteration(strat, {'fast': fast, 'slow': slow})

        # 2. MEAN REVERSION
        strat = self.strategies[1]
        for low in [25, 30]:
            for high in [60, 70]:
                evaluate_iteration(strat, {'rsi_low': low, 'rsi_high': high})

        # 3. BOLLINGER BREAKOUT
        strat = self.strategies[2]
        for win in [20, 30]:
            evaluate_iteration(strat, {'window': win, 'std_dev': 2})

        # 4. MACD
        strat = self.strategies[3]
        evaluate_iteration(strat, {'fast': 12, 'slow': 26, 'signal': 9})

        return global_best_result