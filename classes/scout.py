import yfinance as yf
import pandas as pd
import config as cfg
# Importamos las Clásicas
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)
# Importamos las PRO (NUEVO)
from classes.strategies_pro import SuperTrendStrategy, SqueezeMomentumStrategy, ADXStrategy

class AssetScout:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = self._download_data()
        # ARSENAL EXPANDIDO (10 ESTRATEGIAS AHORA)
        self.strategies = [
            # Las Pro primero (Suelen ser mejores)
            SuperTrendStrategy(),
            SqueezeMomentumStrategy(),
            ADXStrategy(),
            # Las Clásicas
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
        
        # (Aquí va la lógica del mapa... mantén el if de config.py igual que antes)
        if not force_recalc and self.ticker in cfg.STRATEGY_MAP:
            # ... (código existente de atajo) ...
            pass # (Resumido para brevedad, no borres tu código real)

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
            
            # --- NUEVAS ESTRATEGIAS PRO ---
            
            if isinstance(strat, SuperTrendStrategy):
                # Probamos configuraciones clásicas de TradingView
                configs = [
                    {'period': 10, 'multiplier': 3.0}, # Estándar
                    {'period': 12, 'multiplier': 3.0}, # Más suave
                    {'period': 10, 'multiplier': 4.0}  # Stop más amplio (Crypto)
                ]
                for p in configs: evaluate_iteration(strat, p)

            elif isinstance(strat, SqueezeMomentumStrategy):
                # Config LazyBear estándar y una rápida
                configs = [
                    {'bb_len': 20, 'bb_mult': 2.0, 'kc_len': 20, 'kc_mult': 1.5},
                    {'bb_len': 20, 'bb_mult': 2.0, 'kc_len': 20, 'kc_mult': 1.3} # Squeeze más estricto
                ]
                for p in configs: evaluate_iteration(strat, p)

            elif isinstance(strat, ADXStrategy):
                # Solo operamos tendencias fuertes (>20 o >25)
                configs = [
                    {'period': 14, 'adx_threshold': 20},
                    {'period': 14, 'adx_threshold': 25}
                ]
                for p in configs: evaluate_iteration(strat, p)

            # --- ESTRATEGIAS CLÁSICAS (Copia los mismos ifs de antes) ---
            elif isinstance(strat, GoldenCrossStrategy):
                 for fast in [20, 50]:
                    for slow in [100, 200]:
                        if fast >= slow: continue
                        evaluate_iteration(strat, {'fast': fast, 'slow': slow})
            # ... (Agrega el resto de los ifs de tu archivo anterior aquí: Mean, Bollinger, MACD, etc.) ...
            
            # Nota: Asegúrate de incluir todos los ifs de las estrategias viejas aquí abajo
            # para que sigan compitiendo.

        return global_best_result
