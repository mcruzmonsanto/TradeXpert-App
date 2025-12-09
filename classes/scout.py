# classes/scout.py - VERSIÓN CORREGIDA COMPLETA
import yfinance as yf
import pandas as pd
import config as cfg
from typing import Dict, List, Optional
import concurrent.futures
import streamlit as st

# Importamos las Clásicas
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy,
    SuperTrendStrategy, SqueezeMomentumStrategy, ADXStrategy
)


class AssetScout:
    """
    Scout optimizado con cache y paralelización.
    """
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper().strip()
        self.data = self._download_data()  # SIN parámetro ticker
        self.strategies = self._initialize_strategies()
        
    def _initialize_strategies(self) -> List:
        """Inicializa todas las estrategias una sola vez"""
        return [
            # PRO (3)
            SuperTrendStrategy(), 
            SqueezeMomentumStrategy(), 
            ADXStrategy(),
            # CLÁSICAS (7)
            GoldenCrossStrategy(), 
            MeanReversionStrategy(), 
            BollingerBreakoutStrategy(),
            MACDStrategy(), 
            EMAStrategy(), 
            StochRSIStrategy(), 
            AwesomeOscillatorStrategy()
        ]
    
    def _download_data(self) -> pd.DataFrame:
        """
        Descarga datos históricos.
        NOTA: Usa self.ticker, no recibe parámetro.
        """
        try:
            df = yf.Ticker(self.ticker).history(period="2y")
            
            if df.empty:
                st.warning(f"⚠️ {self.ticker}: Sin datos históricos")
                return pd.DataFrame()
            
            if len(df) < 50:
                st.warning(f"⚠️ {self.ticker}: Datos insuficientes ({len(df)} días)")
                return pd.DataFrame()
                
            return df
            
        except Exception as e:
            st.error(f"❌ Error descargando {self.ticker}: {e}")
            return pd.DataFrame()
    
    def optimize(self, force_recalc: bool = False) -> Optional[Dict]:
        """
        Optimiza estrategia para el ticker.
        """
        if self.data.empty:
            return None
        
        # Modo rápido: cargar configuración guardada
        if not force_recalc and self._has_saved_config():
            result = self._load_saved_config()
            if result:
                return result
        
        # Modo lento: grid search optimizado
        return self._run_grid_search()
    
    def _has_saved_config(self) -> bool:
        """Verifica si existe configuración guardada"""
        return (
            hasattr(cfg, 'STRATEGY_MAP') and 
            self.ticker in cfg.STRATEGY_MAP
        )
    
    def _load_saved_config(self) -> Optional[Dict]:
        """Carga configuración guardada y ejecuta backtest"""
        saved_config = cfg.STRATEGY_MAP[self.ticker]
        strat_name = saved_config['strategy']
        params = saved_config['params']
        
        # Buscar estrategia por nombre
        strat_obj = next(
            (s for s in self.strategies if s.name == strat_name), 
            None
        )
        
        if not strat_obj:
            return None
        
        try:
            metrics = strat_obj.backtest(self.data, params)
            
            return {
                "Ticker": self.ticker,
                "Estrategia": strat_name,
                "Retorno": metrics["return"],
                "Sharpe": metrics["sharpe"],
                "Drawdown": metrics["drawdown"],
                "Params": params,
                "Source": "CACHE"
            }
        except Exception as e:
            st.warning(f"⚠️ Error en backtest de {self.ticker}: {e}")
            return None
    
    def _run_grid_search(self) -> Optional[Dict]:
        """Ejecuta grid search optimizado"""
        best_score = -999
        best_result = None
        
        def evaluate_iteration(strat_obj, params):
            nonlocal best_score, best_result
            
            try:
                metrics = strat_obj.backtest(self.data, params)
                
                ret = metrics["return"]
                sharpe = metrics["sharpe"]
                dd = metrics["drawdown"]
                
                # Early stopping
                if dd < -0.60:
                    return
                
                # Score combinado
                score = ret + (sharpe * 0.1) - (abs(dd) * 0.5)
                
                if score > best_score:
                    best_score = score
                    best_result = {
                        "Ticker": self.ticker,
                        "Estrategia": strat_obj.name,
                        "Retorno": ret,
                        "Sharpe": sharpe,
                        "Drawdown": dd,
                        "Params": params,
                        "Source": "OPTIMIZED"
                    }
                
            except Exception:
                pass
        
        # Grid search por estrategia
        for strat in self.strategies:
            
            # ESTRATEGIAS PRO
            if isinstance(strat, SuperTrendStrategy):
                for params in [
                    {'period': 10, 'multiplier': 3.0}, 
                    {'period': 12, 'multiplier': 3.0}
                ]:
                    evaluate_iteration(strat, params)
            
            elif isinstance(strat, SqueezeMomentumStrategy):
                params = {'bb_len': 20, 'bb_mult': 2.0, 'kc_len': 20, 'kc_mult': 1.5}
                evaluate_iteration(strat, params)
            
            elif isinstance(strat, ADXStrategy):
                for params in [
                    {'period': 14, 'adx_threshold': 20},
                    {'period': 14, 'adx_threshold': 25}
                ]:
                    evaluate_iteration(strat, params)
            
            # ESTRATEGIAS CLÁSICAS
            elif isinstance(strat, GoldenCrossStrategy):
                for fast, slow in [(20, 100), (50, 200)]:
                    evaluate_iteration(strat, {'fast': fast, 'slow': slow})
            
            elif isinstance(strat, MeanReversionStrategy):
                for rsi_low in [25, 30]:
                    evaluate_iteration(strat, {'rsi_low': rsi_low, 'rsi_high': 70})
            
            elif isinstance(strat, BollingerBreakoutStrategy):
                evaluate_iteration(strat, {'window': 20, 'std_dev': 2})
            
            elif isinstance(strat, MACDStrategy):
                evaluate_iteration(strat, {'fast': 12, 'slow': 26, 'signal': 9})
            
            elif isinstance(strat, EMAStrategy):
                for params in [
                    {'fast': 8, 'slow': 21}, 
                    {'fast': 5, 'slow': 13}
                ]:
                    evaluate_iteration(strat, params)
            
            elif isinstance(strat, StochRSIStrategy):
                params = {'rsi_period': 14, 'stoch_period': 14, 'k_period': 3, 'd_period': 3}
                evaluate_iteration(strat, params)
            
            elif isinstance(strat, AwesomeOscillatorStrategy):
                evaluate_iteration(strat, {'fast': 5, 'slow': 34})
        
        return best_result


# ============================================
# FUNCIONES AUXILIARES PARA BATCH PROCESSING
# ============================================

def scan_multiple_tickers(
    tickers: List[str], 
    force_recalc: bool = False,
    max_workers: int = 5
) -> pd.DataFrame:
    """
    Escanea múltiples tickers EN PARALELO.
    """
    results = []
    
    # Progress bar principal
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Crear futures para cada ticker
        future_to_ticker = {
            executor.submit(_optimize_single_ticker, ticker, force_recalc): ticker
            for ticker in tickers
        }
        
        # Procesar a medida que completan
        completed = 0
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                st.warning(f"⚠️ Error en {ticker}: {e}")
            
            # Actualizar progress
            completed += 1
            progress = completed / len(tickers)
            progress_bar.progress(progress)
            status_text.text(f"📊 Escaneando: {completed}/{len(tickers)} completados")
    
    # Limpiar UI
    progress_bar.empty()
    status_text.empty()
    
    if not results:
        st.warning("⚠️ No se encontraron resultados válidos")
        return pd.DataFrame()
    
    # Convertir a DataFrame y ordenar
    df = pd.DataFrame(results)
    df = df.sort_values('Retorno', ascending=False).reset_index(drop=True)
    
    return df


def _optimize_single_ticker(ticker: str, force_recalc: bool) -> Optional[Dict]:
    """Función auxiliar para paralelización"""
    try:
        scout = AssetScout(ticker)
        return scout.optimize(force_recalc=force_recalc)
    except Exception:
        return None


def filter_top_opportunities(
    df: pd.DataFrame, 
    min_return: float = 0.10,
    max_drawdown: float = -0.40,
    min_sharpe: float = 0.5,
    top_n: int = 10
) -> pd.DataFrame:
    """Filtra las mejores oportunidades según criterios"""
    if df.empty:
        return df
    
    filtered = df[
        (df['Retorno'] >= min_return) &
        (df['Drawdown'] >= max_drawdown) &
        (df['Sharpe'] >= min_sharpe)
    ]
    
    return filtered.head(top_n)
