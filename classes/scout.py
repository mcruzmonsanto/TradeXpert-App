import yfinance as yf
import pandas as pd
# IMPORTAMOS TODAS LAS ESTRATEGIAS
from classes.strategies import (
    GoldenCrossStrategy, 
    MeanReversionStrategy, 
    BollingerBreakoutStrategy, 
    MACDStrategy,
    EMAStrategy,
    StochRSIStrategy,
    AwesomeOscillatorStrategy
)

class AssetScout:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = self._download_data()
        # Cargamos el arsenal completo (7 estrategias)
        self.strategies = [
            GoldenCrossStrategy(), 
            MeanReversionStrategy(),
            BollingerBreakoutStrategy(),
            MACDStrategy(),
            EMAStrategy(),
            StochRSIStrategy(),
            AwesomeOscillatorStrategy()
        ]

    def _download_data(self):
        try:
            df = yf.Ticker(self.ticker).history(period="5y")
            return df
        except:
            return pd.DataFrame()

    def optimize(self):
        if self.data.empty: return None
        
        global_best_score = -999
        global_best_result = None

        def evaluate_iteration(strat_obj, params):
            nonlocal global_best_score, global_best_result
            metrics = strat_obj.backtest(self.data, params)
            
            ret = metrics["return"]
            sharpe = metrics["sharpe"]
            dd = metrics["drawdown"]
            
            # Filtro de Seguridad: Si pierde más del 60%, descartado
            if dd < -0.60: return

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

        # --- BUCLE DINÁMICO (AQUI ESTABA EL ERROR) ---
        # Ahora recorremos la lista, sin importar si tiene 1 estrategia o 7
        
        for strat in self.strategies:
            
            # 1. GOLDEN CROSS
            if isinstance(strat, GoldenCrossStrategy):
                for fast in [20, 50]:
                    for slow in [100, 200]:
                        if fast >= slow: continue
                        evaluate_iteration(strat, {'fast': fast, 'slow': slow})

            # 2. MEAN REVERSION
            elif isinstance(strat, MeanReversionStrategy):
                for low in [25, 30]:
                    for high in [60, 70]:
                        evaluate_iteration(strat, {'rsi_low': low, 'rsi_high': high})

            # 3. BOLLINGER
            elif isinstance(strat, BollingerBreakoutStrategy):
                for win in [20, 30]:
                    evaluate_iteration(strat, {'window': win, 'std_dev': 2})

            # 4. MACD
            elif isinstance(strat, MACDStrategy):
                evaluate_iteration(strat, {'fast': 12, 'slow': 26, 'signal': 9})

            # 5. EMA CROSSOVER
            elif isinstance(strat, EMAStrategy):
                configs = [{'fast': 8, 'slow': 21}, {'fast': 9, 'slow': 21}, {'fast': 5, 'slow': 13}]
                for params in configs:
                    evaluate_iteration(strat, params)

            # 6. STOCHASTIC RSI
            elif isinstance(strat, StochRSIStrategy):
                configs = [
                    {'rsi_period': 14, 'stoch_period': 14, 'k_period': 3, 'd_period': 3},
                    {'rsi_period': 9, 'stoch_period': 9, 'k_period': 3, 'd_period': 3}
                ]
                for params in configs:
                    evaluate_iteration(strat, params)

            # 7. AWESOME OSCILLATOR
            elif isinstance(strat, AwesomeOscillatorStrategy):
                configs = [{'fast': 5, 'slow': 34}, {'fast': 3, 'slow': 10}]
                for params in configs:
                    evaluate_iteration(strat, params)

        return global_best_result
