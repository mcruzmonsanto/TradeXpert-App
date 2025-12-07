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

# --- BARRA LATERAL (CONTROLES DE DINERO) ---
st.sidebar.header("💰 Gestión de Capital")

# 1. Input para modificar Capital (Por defecto carga el de config.py)
capital_dinamico = st.sidebar.number_input(
    "Capital Disponible ($)", 
    min_value=100.0, 
    max_value=1000000.0, 
    value=float(cfg.CAPITAL_TOTAL), 
    step=500.0,
    help="Dinero total en tu cuenta de broker para calcular el tamaño de posición."
)

# 2. Input para modificar Riesgo (Slider de 0.5% a 10%)
riesgo_pct = st.sidebar.slider(
    "Riesgo por Operación (%)", 
    min_value=0.5, 
    max_value=10.0, 
    value=float(cfg.RIESGO_POR_OPERACION * 100), 
    step=0.5,
    help="Porcentaje de tu capital que estás dispuesto a perder si toca el Stop Loss."
)
# Convertimos el porcentaje visual (ej: 2.0) a decimal matemático (0.02)
riesgo_decimal = riesgo_pct / 100.0


# --- FUNCIÓN DE GUARDADO (DATABASE) ---
LOG_FILE = "data/bitacora_trades.csv"

def guardar_trade(trade_dict):
    if not os.path.exists("data"):
        os.makedirs("data")
        
    if os.path.exists(LOG_FILE):
        df_log = pd.read_csv(LOG_FILE)
    else:
        df_log = pd.DataFrame(columns=["Fecha", "Ticker", "Accion", "Estrategia", "Precio_Entrada", "Unidades", "Inversion", "Stop_Loss", "Take_Profit", "Status", "Precio_Salida", "Resultado"])
    
    new_row = pd.DataFrame([trade_dict])
    df_log = pd.concat([df_log, new_row], ignore_index=True)
    df_log.to_csv(LOG_FILE, index=False)
    return True

# --- INTERFAZ PRINCIPAL ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("📡 Radar: Ejecución y Registro")
    # Mostramos los valores dinámicos que seleccionó el usuario
    st.markdown(f"Capital: **${capital_dinamico:,.2f}** | Riesgo: **{riesgo_pct}%**")
    
    # Cálculo rápido de cuánto es el dinero en riesgo
    dinero_en_riesgo = capital_dinamico * riesgo_decimal
    st.caption(f"🔥 Estás arriesgando máximo **${dinero_en_riesgo:.2f}** por operación.")

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
                
                # --- CLASIFICACIÓN ---
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
                        # USAMOS LOS VALORES DINÁMICOS DE LA BARRA LATERAL
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
                                    * 📦 Unidades: **{units:.4f}** (Inv: ${inv:.2f})
                                    * 🛡️ Stop Loss: **${sl:.2f}**
                                    * 🎯 Take Profit: **${tp:.2f}**
                                    """)
                            
                            with c_action:
                                st.write("") 
                                st.write("")
                                if es_oportunidad_valida:
                                    # BOTÓN DE REGISTRO
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
            pass 
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.empty()
    progress_bar.empty()
    
    if conteo == 0:
        st.info("Sin señales activas hoy.")
