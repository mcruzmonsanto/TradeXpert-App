# classes/scout.py
import yfinance as yf
import pandas as pd
import config as cfg # Importamos la configuración maestra
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)

class AssetScout:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = self._download_data()
        self.strategies = [
            GoldenCrossStrategy(), MeanReversionStrategy(), BollingerBreakoutStrategy(),
            MACDStrategy(), EMAStrategy(), StochRSIStrategy(), AwesomeOscillatorStrategy()
        ]

    def _download_data(self):
        try:
            # Bajamos solo 2 años para velocidad operativa (suficiente para señales diarias)
            # Si quisieras re-optimizar a fondo, usarías 5y
            df = yf.Ticker(self.ticker).history(period="2y")
            return df
        except:
            return pd.DataFrame()

    def optimize(self, force_recalc=False):
        """
        force_recalc: Si es False, usa el mapa maestro de config.py (Instantáneo).
                      Si es True, vuelve a probar todo (Lento).
        """
        if self.data.empty: return None
        
        # --- ATAJO MAESTRO ---
        # Si NO forzamos recálculo y el ticker está en el mapa, lo usamos directo.
        if not force_recalc and self.ticker in cfg.STRATEGY_MAP:
            saved_config = cfg.STRATEGY_MAP[self.ticker]
            strat_name = saved_config['strategy']
            params = saved_config['params']
            
            # Buscamos el objeto de estrategia correcto
            strat_obj = next((s for s in self.strategies if s.name == strat_name), None)
            
            if strat_obj:
                # Corremos backtest rápido solo para sacar métricas actuales
                metrics = strat_obj.backtest(self.data, params)
                return {
                    "Ticker": self.ticker,
                    "Estrategia": strat_name,
                    "Retorno": metrics["return"],
                    "Sharpe": metrics["sharpe"],
                    "Drawdown": metrics["drawdown"],
                    "Params": params
                }

        # --- MODO LENTO (SI NO HAY MAPA O SE FUERZA) ---
        # (Aquí va todo tu código de bucles for anterior... MANTENLO IGUAL)
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

        # BUCLES FOR (Copia los mismos de tu archivo anterior)
        # ...
        # (Para brevedad, asumo que mantienes los bucles for aquí)
        # ...
        
        # Si no tienes los bucles a mano, dímelo y te paso el archivo completo de nuevo.
        # Pero la idea es que si entra al "if" del principio, se salta todo esto.
        
        # Bucle de rescate si no encontró nada
        if not global_best_result: return None
            
        return global_best_result
