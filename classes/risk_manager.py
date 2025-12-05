# classes/risk_manager.py
import pandas as pd
import numpy as np

class RiskManager:
    def __init__(self, df):
        self.df = df
        
    def calculate_atr(self, period=14):
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
        atr_series = self.calculate_atr()
        current_atr = atr_series.iloc[-1]
        
        if pd.isna(current_atr) or current_atr == 0:
            return None

        stop_loss = 0
        take_profit = 0
        
        # Lógica para COMPRA (Long)
        if direction == "LONG":
            stop_loss = entry_price - (current_atr * atr_multiplier)
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * risk_reward_ratio)
            
        # Lógica para VENTA EN CORTO (Short)
        elif direction == "SHORT":
            # En Short, el Stop Loss está POR ENCIMA del precio de entrada
            stop_loss = entry_price + (current_atr * atr_multiplier)
            # El riesgo es la distancia hacia arriba
            risk = stop_loss - entry_price
            # El Take Profit está POR DEBAJO (queremos que baje)
            take_profit = entry_price - (risk * risk_reward_ratio)
            
        return {
            "entry": entry_price,
            "direction": direction,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "atr": current_atr,
            "risk_per_share": risk,
            "potential_gain": risk * risk_reward_ratio,
            "rr_ratio": risk_reward_ratio
        }

    def calculate_position_size(self, account_size, risk_pct_per_trade, trade_setup):
        """
        Calcula unidades exactas (CFDs fraccionados).
        """
        if not trade_setup: return 0.0
        
        # Capital en riesgo (Ej: $200)
        risk_amount = account_size * risk_pct_per_trade
        
        risk_per_share = trade_setup['risk_per_share']
        
        if risk_per_share <= 0: return 0.0
        
        # --- CAMBIO CRÍTICO: USAMOS FLOAT, NO INT ---
        # Si riesgo total es $200 y riesgo por acción es $50, compramos 4.0
        # Si riesgo por acción es $500 (ej: BTC se mueve mucho), compramos 0.4
        units = risk_amount / risk_per_share
        
        # Validación de apalancamiento máximo:
        # Aunque sean CFDs, asumimos que no queremos usar apalancamiento excesivo (1:1 o máximo 1:2 implícito)
        # Calculamos cuántas unidades podríamos comprar con TODO el capital
        max_units_by_capital = account_size / trade_setup['entry']
        
        # Por seguridad, si el cálculo de riesgo pide comprar más de lo que tenemos en cash,
        # limitamos al máximo de cash (Equity).
        # (Si quisieras apalancamiento, quitarías esta línea o multiplicarías max_units * 2 o * 5)
        final_units = min(units, max_units_by_capital)
        
        return round(final_units, 4) # Devolvemos con 4 decimales