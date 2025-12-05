# classes/risk_manager.py
import pandas as pd
import numpy as np

class RiskManager:
    def __init__(self, df):
        self.df = df
        
    def calculate_atr(self, period=14):
        """Calcula el Average True Range (Volatilidad)"""
        high = self.df['High']
        low = self.df['Low']
        close = self.df['Close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def get_trade_setup(self, entry_price, direction="LONG", atr_multiplier=2.0, risk_reward_ratio=2.0):
        """
        Define los niveles de salida (Stop Loss y Take Profit) basados en volatilidad.
        """
        atr_series = self.calculate_atr()
        current_atr = atr_series.iloc[-1]
        
        if pd.isna(current_atr) or current_atr == 0:
            return None

        stop_loss = 0
        take_profit = 0
        
        if direction == "LONG":
            # Stop Loss: Precio - (2 veces la volatilidad)
            stop_loss = entry_price - (current_atr * atr_multiplier)
            
            # Riesgo por acción
            risk_per_share = entry_price - stop_loss
            
            # Take Profit: Precio + (2 veces el riesgo)
            take_profit = entry_price + (risk_per_share * risk_reward_ratio)
            
        return {
            "entry": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "atr": current_atr,
            "risk_per_share": entry_price - stop_loss,
            "potential_gain": take_profit - entry_price,
            "rr_ratio": risk_reward_ratio
        }

    def calculate_position_size(self, account_size, risk_pct_per_trade, trade_setup):
        """
        Calcula cuántas acciones comprar para respetar el riesgo máximo.
        """
        if not trade_setup: return 0
        
        # Dinero que estamos dispuestos a perder (Ej: 2% de $10,000 = $200)
        risk_amount = account_size * risk_pct_per_trade
        
        # Riesgo por acción (Ej: Entro en $100, Stop en $95 -> Riesgo $5)
        risk_per_share = trade_setup['risk_per_share']
        
        if risk_per_share <= 0: return 0
        
        # Acciones a comprar: $200 / $5 = 40 acciones
        shares = int(risk_amount / risk_per_share)
        
        # Validación: No podemos comprar más de lo que nos permite el capital total
        max_shares_by_capital = int(account_size / trade_setup['entry'])
        
        return min(shares, max_shares_by_capital)