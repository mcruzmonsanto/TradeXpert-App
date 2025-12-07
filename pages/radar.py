# pages/radar.py
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

sys.path.append('.') 
from classes.scout import AssetScout
# Importamos las Clásicas
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)
# Importamos las PRO (NUEVO)
from classes.strategies_pro import SuperTrendStrategy, SqueezeMomentumStrategy, ADXStrategy
from classes.risk_manager import RiskManager
import config as cfg

st.set_page_config(page_title="Radar Pro V11", layout="wide", page_icon="📡")

# --- BARRA LATERAL (CONTROLES) ---
st.sidebar.header("💰 Gestión de Capital")
capital_dinamico = st.sidebar.number_input("Capital ($)", 100.0, 1000000.0, float(cfg.CAPITAL_TOTAL), 500.0)
riesgo_pct = st.sidebar.slider("Riesgo (%)", 0.5, 10.0, float(cfg.RIESGO_POR_OPERACION * 100), 0.5)
riesgo_decimal = riesgo_pct / 100.0

# --- BASE DE DATOS ---
LOG_FILE = "data/bitacora_trades.csv"

def guardar_trade(trade_dict):
    if not os.path.exists("data"): os.makedirs("data")
    if os.path.exists(LOG_FILE):
        df_log = pd.read_csv(LOG_FILE)
    else:
        df_log = pd.DataFrame(columns=["Fecha", "Ticker", "Accion", "Estrategia", "Precio_Entrada", "Unidades", "Inversion", "Stop_Loss", "Take_Profit", "Status", "Precio_Salida", "Resultado"])
    
    new_row = pd.DataFrame([trade_dict])
    df_log = pd.concat([df_log, new_row], ignore_index=True)
    df_log.to_csv(LOG_FILE, index=False)
    return True

# --- INTERFAZ ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("📡 Radar: Centro de Mando Pro")
    st.markdown(f"Capital: **${capital_dinamico:,.2f}** | Riesgo: **{riesgo_pct}%**")
    st.caption("Escaneando con 10 Motores de Inteligencia Artificial")

with c2:
    st.markdown("### ⚙️ Filtros")
    solo_accion = st.checkbox("Ocultar 'Mantener'", value=True)

if st.button("🚀 INICIAR ESCANEO PRO"):
    
    st.markdown("---")
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()

    total_assets = len(cfg.TICKERS)
    conteo = 0
    
    for i, ticker in enumerate(cfg.TICKERS):
        status_text.text(f"Analizando {ticker} ({i+1}/{total_assets})...")
        
        try:
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            if winner and scout.data is not None and not scout.data.empty:
                df = scout.data.copy()
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # --- INSTANCIADOR INTELIGENTE (10 MOTORES) ---
                strat_obj = None
                if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
                elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
                elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
                elif "MACD" in strat_name: strat_obj = MACDStrategy()
                elif "EMA" in strat_name: strat_obj = EMAStrategy()
                elif "Stochastic" in strat_name: strat_obj = StochRSIStrategy()
                elif "Awesome" in strat_name: strat_obj = AwesomeOscillatorStrategy()
                # Nuevas PRO
                elif "SuperTrend" in strat_name: strat_obj = SuperTrendStrategy()
                elif "Squeeze" in strat_name: strat_obj = SqueezeMomentumStrategy()
                elif "ADX" in strat_name: strat_obj = ADXStrategy()
                
                df = strat_obj.generate_signals(df, params)
                if 'Signal' not in df.columns: df['Signal'] = 0
                
                today = df.iloc[-1]
                prev = df.iloc[-2]
                signal_val = today['Signal']
                
                tipo = "NEUTRO"
                direction = "NONE"
                es_oportunidad_valida = False
                
                # --- CLASIFICACIÓN DE SEÑALES ---
                
                # A) LÓGICA LONG (COMPRA)
                if signal_val == 1:
                    is_new = (prev['Signal'] == 0)
                    
                    # Estrategias Clásicas
                    if "Golden Cross" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "ENTRADA CRUCE", "LONG", True
                        else: tipo = "MANTENER TENDENCIA"
                    elif "Mean Reversion" in strat_name:
                        tipo, direction, es_oportunidad_valida = "ENTRADA REBOTE", "LONG", True
                    elif "MACD" in strat_name:
                        tipo, direction, es_oportunidad_valida = "ENTRADA MOMENTUM", "LONG", True
                    elif "EMA" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "ENTRADA EMA", "LONG", True
                        else: tipo = "MANTENER EMA"
                    elif "Stochastic" in strat_name:
                        if is_new and today['Stoch_K'] < 50: tipo, direction, es_oportunidad_valida = "ENTRADA STOCH", "LONG", True
                        else: tipo = "MANTENER STOCH"
                    elif "Awesome" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "ENTRADA AO", "LONG", True
                        else: tipo = "MANTENER AO"
                    
                    # Estrategias PRO
                    elif "SuperTrend" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "CAMBIO TENDENCIA (SUPER)", "LONG", True
                        else: tipo = "MANTENER SUPERTREND"
                    elif "Squeeze" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "DISPARO SQUEEZE 🔥", "LONG", True
                        else: tipo = "MANTENER SQUEEZE"
                    elif "ADX" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "INICIO TENDENCIA FUERTE", "LONG", True
                        else: tipo = "MANTENER TENDENCIA ADX"
                    elif "Bollinger" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "RUPTURA ALCISTA", "LONG", True
                        else: tipo = "MANTENER RUPTURA"

                # B) LÓGICA SHORT (VENTA)
                elif signal_val == 0:
                    # Mean Reversion Short
                    if "Mean Reversion" in strat_name and today['RSI'] > params['rsi_high']:
                        tipo, direction, es_oportunidad_valida = "ENTRADA SHORT (SOBRECOMPRA)", "SHORT", True
                    
                    # Stoch Short
                    elif "Stochastic" in strat_name and today['Stoch_K'] > 80 and today['Stoch_K'] < today['Stoch_D']:
                        tipo, direction, es_oportunidad_valida = "ENTRADA SHORT (STOCH)", "SHORT", True
                    
                    # EMA Short
                    elif "EMA" in strat_name:
                        ema_fast = df['EMA_Fast'].iloc[-1]
                        ema_slow = df['EMA_Slow'].iloc[-1]
                        if ema_fast < ema_slow and df['EMA_Fast'].iloc[-2] >= df['EMA_Slow'].iloc[-2]:
                            tipo, direction, es_oportunidad_valida = "ENTRADA SHORT (EMA)", "SHORT", True

                    # SuperTrend Short
                    elif "SuperTrend" in strat_name and prev['Signal'] == 1:
                        tipo, direction, es_oportunidad_valida = "CAMBIO TENDENCIA (SHORT)", "SHORT", True

                    # Squeeze Short (Momentum negativo)
                    elif "Squeeze" in strat_name:
                        if df['Momentum'].iloc[-1] < 0 and df['Momentum'].iloc[-2] >= 0:
                            tipo, direction, es_oportunidad_valida = "MOMENTUM BAJISTA", "SHORT", True

                # --- RENDERIZADO ---
                mostrar = False
                if solo_accion:
                    if es_oportunidad_valida: mostrar = True
                elif tipo != "NEUTRO": mostrar = True

                if mostrar:
                    conteo += 1
                    
                    # Cálculo de Riesgo
                    risk_mgr = RiskManager(df)
                    setup = risk_mgr.get_trade_setup(
                        entry_price=today['Close'], 
                        direction=direction if direction != "NONE" else "LONG", 
                        atr_multiplier=cfg.ATR_MULTIPLIER, 
                        risk_reward_ratio=cfg.RR_RATIO
                    )
                    
                    units = 0.0
                    inv = 0.0
                    sl, tp = 0.0, 0.0
                    
                    if setup and es_oportunidad_valida:
                        units = risk_mgr.calculate_position_size(capital_dinamico, riesgo_decimal, setup)
                        inv = units * today['Close']
                        sl = setup['stop_loss']
                        tp = setup['take_profit']
                    
                    with results_container:
                        color_border = "green" if direction == "LONG" else "red" if direction == "SHORT" else "blue"
                        with st.container(border=True):
                            c_info, c_action = st.columns([3, 1])
                            
                            with c_info:
                                icon = "🟢" if direction == "LONG" else "🔻" if direction == "SHORT" else "🔵"
                                st.markdown(f"### {icon} {ticker} | {tipo}")
                                st.caption(f"Estrategia: {strat_name} | Precio: ${today['Close']:.2f}")
                                
                                if es_oportunidad_valida:
                                    st.markdown(f"""
                                    **EJECUCIÓN {direction}:**
                                    * 📦 Unidades: **{units:.4f}** (Inv: ${inv:,.2f})
                                    * 🛡️ Stop Loss: **${sl:.2f}**
                                    * 🎯 Take Profit: **${tp:.2f}**
                                    """)
                            
                            with c_action:
                                st.write("") 
                                st.write("")
                                if es_oportunidad_valida:
                                    # BOTÓN DE REGISTRO
                                    btn_key = f"save_{ticker}_{datetime.now().strftime('%H%M%S')}"
                                    if st.button(f"💾 Registrar", key=btn_key, type="primary"):
                                        trade_data = {
                                            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                            "Ticker": ticker,
                                            "Accion": direction,
                                            "Estrategia": strat_name,
                                            "Precio_Entrada": round(today['Close'], 2),
                                            "Unidades": units,
                                            "Inversion": round(inv, 2),
                                            "Stop_Loss": round(sl, 2),
                                            "Take_Profit": round(tp, 2),
                                            "Status": "ABIERTA",
                                            "Precio_Salida": 0.0,
                                            "Resultado": 0.0
                                        }
                                        guardar_trade(trade_data)
                                        st.toast(f"✅ Orden de {ticker} guardada!")

        except Exception as e:
            # pass 
            st.error(f"Error en {ticker}: {e}")
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.empty()
    progress_bar.empty()
    
    if conteo == 0:
        st.info("Sin señales activas hoy. El mercado está decidiendo dirección.")
