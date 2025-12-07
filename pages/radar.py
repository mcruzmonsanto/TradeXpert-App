# pages/radar.py
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)
from classes.risk_manager import RiskManager
import config as cfg

st.set_page_config(page_title="Radar & Ejecución", layout="wide", page_icon="📡")

# --- FUNCIÓN DE GUARDADO (DATABASE) ---
LOG_FILE = "data/bitacora_trades.csv"

def guardar_trade(trade_dict):
    # Verificar si existe la carpeta data
    if not os.path.exists("data"):
        os.makedirs("data")
        
    # Verificar si existe el archivo para cargar o crear cabeceras
    if os.path.exists(LOG_FILE):
        df_log = pd.read_csv(LOG_FILE)
    else:
        df_log = pd.DataFrame(columns=["Fecha", "Ticker", "Accion", "Estrategia", "Precio_Entrada", "Unidades", "Inversion", "Stop_Loss", "Take_Profit", "Status", "Precio_Salida", "Resultado"])
    
    # Agregar nueva fila
    new_row = pd.DataFrame([trade_dict])
    df_log = pd.concat([df_log, new_row], ignore_index=True)
    df_log.to_csv(LOG_FILE, index=False)
    return True

# --- INTERFAZ ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("📡 Radar: Ejecución y Registro")
    st.markdown(f"Capital: **${cfg.CAPITAL_TOTAL}** | Riesgo: **{cfg.RIESGO_POR_OPERACION*100}%**")

with c2:
    st.markdown("### ⚙️ Filtros")
    solo_accion = st.checkbox("Ocultar 'Mantener'", value=True)

if st.button("🚀 INICIAR ESCANEO Y EJECUCIÓN"):
    
    st.markdown("---")
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()

    total_assets = len(cfg.TICKERS)
    conteo = 0
    
    for i, ticker in enumerate(cfg.TICKERS):
        status_text.text(f"Analizando {ticker} ({i+1}/{total_assets})...")
        
        try:
            # 1. Optimización (Usando el mapa rápido de config)
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            if winner and scout.data is not None and not scout.data.empty:
                df = scout.data.copy()
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # 2. Instanciar
                strat_obj = None
                if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
                elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
                elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
                elif "MACD" in strat_name: strat_obj = MACDStrategy()
                elif "EMA" in strat_name: strat_obj = EMAStrategy()
                elif "Stochastic" in strat_name: strat_obj = StochRSIStrategy()
                elif "Awesome" in strat_name: strat_obj = AwesomeOscillatorStrategy()
                
                df = strat_obj.generate_signals(df, params)
                if 'Signal' not in df.columns: df['Signal'] = 0
                
                today = df.iloc[-1]
                prev = df.iloc[-2]
                signal_val = today['Signal']
                
                tipo = "NEUTRO"
                direction = "NONE"
                es_oportunidad_valida = False
                
                # --- CLASIFICACIÓN (Simplificada para brevedad) ---
                if signal_val == 1:
                    is_new = (prev['Signal'] == 0)
                    if "Golden Cross" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "ENTRADA CRUCE", "LONG", True
                        else: tipo = "MANTENER"
                    elif "Bollinger" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "ENTRADA RUPTURA", "LONG", True
                        else: tipo = "MANTENER"
                    elif "Mean Reversion" in strat_name:
                        tipo, direction, es_oportunidad_valida = "ENTRADA REBOTE", "LONG", True
                    elif "MACD" in strat_name:
                        tipo, direction, es_oportunidad_valida = "ENTRADA MOMENTUM", "LONG", True
                    elif "EMA" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "ENTRADA EMA", "LONG", True
                        else: tipo = "MANTENER"
                    elif "Stochastic" in strat_name:
                        if is_new and today['Stoch_K'] < 50: tipo, direction, es_oportunidad_valida = "ENTRADA STOCH", "LONG", True
                        else: tipo = "MANTENER"
                    elif "Awesome" in strat_name:
                        if is_new: tipo, direction, es_oportunidad_valida = "ENTRADA AO", "LONG", True
                        else: tipo = "MANTENER"

                elif signal_val == 0:
                    if "Mean Reversion" in strat_name and today['RSI'] > params['rsi_high']:
                        tipo, direction, es_oportunidad_valida = "ENTRADA SHORT", "SHORT", True
                    elif "Stochastic" in strat_name and today['Stoch_K'] > 80 and today['Stoch_K'] < today['Stoch_D']:
                        tipo, direction, es_oportunidad_valida = "ENTRADA SHORT", "SHORT", True
                    # (Puedes agregar más lógicas de short aquí)

                # --- RENDERIZADO ---
                mostrar = False
                if solo_accion:
                    if es_oportunidad_valida: mostrar = True
                elif tipo != "NEUTRO": mostrar = True

                if mostrar:
                    conteo += 1
                    
                    # Riesgo
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
                        units = risk_mgr.calculate_position_size(cfg.CAPITAL_TOTAL, cfg.RIESGO_POR_OPERACION, setup)
                        inv = units * today['Close']
                        sl = setup['stop_loss']
                        tp = setup['take_profit']
                    
                    with results_container:
                        # Marco visual
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
                                    * 📦 Unidades: **{units:.4f}** (Inv: ${inv:.2f})
                                    * 🛡️ Stop Loss: **${sl:.2f}**
                                    * 🎯 Take Profit: **${tp:.2f}**
                                    """)
                            
                            with c_action:
                                st.write("") # Espacio
                                st.write("")
                                if es_oportunidad_valida:
                                    # BOTÓN DE REGISTRO
                                    # Usamos un key único para que no se confundan los botones
                                    btn_key = f"save_{ticker}_{datetime.now().strftime('%H%M')}"
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
                                        st.toast(f"✅ Orden de {ticker} guardada en Bitácora!")

        except Exception as e:
            pass # st.error(e)
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.empty()
    progress_bar.empty()
    
    if conteo == 0:
        st.info("Sin señales activas hoy.")
