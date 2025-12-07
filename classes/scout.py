import yfinance as yf
import pandas as pd
import config as cfg
# Importamos las Clásicas
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)
# Importamos las PRO (CRUCIAL PARA QUE FUNCIONE)
from classes.strategies_pro import SuperTrendStrategy, SqueezeMomentumStrategy, ADXStrategy

class AssetScout:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = self._download_data()
        # ARSENAL DE 10 ESTRATEGIAS
        self.strategies = [
            SuperTrendStrategy(), SqueezeMomentumStrategy(), ADXStrategy(),
            GoldenCrossStrategy(), MeanReversionStrategy(), BollingerBreakoutStrategy(),
            MACDStrategy(), EMAStrategy(), StochRSIStrategy(), AwesomeOscillatorStrategy()
        ]

    def _download_data(self):
        try:
            df = yf.Ticker(self.ticker).history(period="2y")
            return df
        except:
            return pd.DataFrame()

    def optimize(self, force_recalc=False):
        if self.data.empty: return None
        
        # ATAJO MAESTRO (Memoria)
        if not force_recalc and hasattr(cfg, 'STRATEGY_MAP') and self.ticker in cfg.STRATEGY_MAP:
            saved_config = cfg.STRATEGY_MAP[self.ticker]
            strat_name = saved_config['strategy']
            params = saved_config['params']
            
            # Buscar la estrategia en la lista por nombre
            strat_obj = next((s for s in self.strategies if s.name == strat_name), None)
            
            if strat_obj:
                metrics = strat_obj.backtest(self.data, params)
                return {
                    "Ticker": self.ticker,
                    "Estrategia": strat_name,
                    "Retorno": metrics["return"],
                    "Sharpe": metrics["sharpe"],
                    "Drawdown": metrics["drawdown"],
                    "Params": params
                }

        # MODO LENTO (Optimización)
        global_best_score = -999
        global_best_result = None

        def evaluate_iteration(strat_obj, params):
            nonlocal global_best_score, global_best_result
            metrics = strat_obj.backtest(self.data, params)
            ret = metrics["return"]
            sharpe = metrics["sharpe"]
            dd = metrics["drawdown"]
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

        for strat in self.strategies:
            # ESTRATEGIAS PRO
            if isinstance(strat, SuperTrendStrategy):
                for p in [{'period': 10, 'multiplier': 3.0}, {'period': 12, 'multiplier': 3.0}]: evaluate_iteration(strat, p)
            elif isinstance(strat, SqueezeMomentumStrategy):
                for p in [{'bb_len': 20, 'bb_mult': 2.0, 'kc_len': 20, 'kc_mult': 1.5}]: evaluate_iteration(strat, p)
            elif isinstance(strat, ADXStrategy):
                for p in [{'period': 14, 'adx_threshold': 20}]: evaluate_iteration(strat, p)
            
            # ESTRATEGIAS CLÁSICAS
            elif isinstance(strat, GoldenCrossStrategy):
                 for fast in [20, 50]:
                    for slow in [100, 200]:
                        if fast < slow: evaluate_iteration(strat, {'fast': fast, 'slow': slow})
            elif isinstance(strat, MeanReversionStrategy):
                for low in [25, 30]: evaluate_iteration(strat, {'rsi_low': low, 'rsi_high': 70})
            elif isinstance(strat, BollingerBreakoutStrategy):
                evaluate_iteration(strat, {'window': 20, 'std_dev': 2})
            elif isinstance(strat, MACDStrategy):
                evaluate_iteration(strat, {'fast': 12, 'slow': 26, 'signal': 9})
            elif isinstance(strat, EMAStrategy):
                for p in [{'fast': 8, 'slow': 21}, {'fast': 5, 'slow': 13}]: evaluate_iteration(strat, p)
            elif isinstance(strat, StochRSIStrategy):
                evaluate_iteration(strat, {'rsi_period': 14, 'stoch_period': 14, 'k_period': 3, 'd_period': 3})
            elif isinstance(strat, AwesomeOscillatorStrategy):
                evaluate_iteration(strat, {'fast': 5, 'slow': 34})

        return global_best_result
