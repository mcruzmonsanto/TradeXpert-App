# classes/risk_manager.py - VERSIÓN OPTIMIZADA
import pandas as pd
import numpy as np
from typing import Dict, Optional

class RiskManager:
    """Gestor de riesgo optimizado con cálculos vectorizados"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._atr_cache = {}
        self._validate_dataframe()
    
    def _validate_dataframe(self):
        required_cols = ['High', 'Low', 'Close']
        missing = [col for col in required_cols if col not in self.df.columns]
        if missing:
            raise ValueError(f"Faltan columnas: {missing}")
        if len(self.df) < 14:
            raise ValueError(f"DataFrame muy pequeño ({len(self.df)} filas)")
    
    def calculate_atr(self, period: int = 14) -> pd.Series:
        """Calcula ATR vectorizado con cache"""
        cache_key = f"atr_{period}"
        if cache_key in self._atr_cache:
            return self._atr_cache[cache_key]
        
        high = self.df['High'].values
        low = self.df['Low'].values
        close_prev = self.df['Close'].shift(1).values
        
        tr1 = high - low
        tr2 = np.abs(high - close_prev)
        tr3 = np.abs(low - close_prev)
        
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        atr = pd.Series(tr).rolling(window=period, min_periods=1).mean()
        
        self._atr_cache[cache_key] = atr
        return atr
    
    def get_trade_setup(
        self, 
        entry_price: float, 
        direction: str = "LONG", 
        atr_multiplier: float = 2.0, 
        risk_reward_ratio: float = 2.0
    ) -> Optional[Dict[str, float]]:
        """Calcula setup completo de un trade"""
        
        if direction not in ["LONG", "SHORT"]:
            raise ValueError(f"Dirección inválida: {direction}")
        if entry_price <= 0:
            raise ValueError(f"Precio inválido: {entry_price}")
        
        atr_series = self.calculate_atr()
        current_atr = atr_series.iloc[-1]
        
        if pd.isna(current_atr) or current_atr <= 0:
            return None
        
        if direction == "LONG":
            stop_loss = entry_price - (current_atr * atr_multiplier)
            risk_per_share = entry_price - stop_loss
            take_profit = entry_price + (risk_per_share * risk_reward_ratio)
        else:  # SHORT
            stop_loss = entry_price + (current_atr * atr_multiplier)
            risk_per_share = stop_loss - entry_price
            take_profit = entry_price - (risk_per_share * risk_reward_ratio)
        
        if risk_per_share <= 0:
            return None
        
        return {
            "entry": round(entry_price, 2),
            "direction": direction,
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "atr": round(current_atr, 2),
            "risk_per_share": round(risk_per_share, 2),
            "potential_gain": round(risk_per_share * risk_reward_ratio, 2),
            "rr_ratio": risk_reward_ratio
        }
    
    def calculate_position_size(
        self, 
        account_size: float, 
        risk_pct_per_trade: float, 
        trade_setup: Optional[Dict]
    ) -> float:
        """Calcula tamaño de posición óptimo (CFDs fraccionados)"""
        
        if not trade_setup:
            return 0.0
        
        if account_size <= 0:
            raise ValueError(f"account_size debe ser > 0")
        if not (0 < risk_pct_per_trade <= 0.1):
            raise ValueError(f"risk_pct_per_trade fuera de rango")
        
        risk_amount = account_size * risk_pct_per_trade
        risk_per_share = trade_setup['risk_per_share']
        
        if risk_per_share <= 0:
            return 0.0
        
        units_by_risk = risk_amount / risk_per_share
        max_units_by_capital = account_size / trade_setup['entry']
        final_units = min(units_by_risk, max_units_by_capital)
        
        return round(final_units, 4)
