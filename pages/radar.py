import streamlit as st
import pandas as pd
import sys

sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)
from classes.risk_manager import RiskManager
import config as cfg

st.set_page_config(page_title="Radar Completo", layout="wide", page_icon="📡")

# --- ENCABEZADO ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("📡 Radar Visual: Plan de Trading")
    st.markdown(f"Capital: **${cfg.CAPITAL_TOTAL}** | Riesgo: **{cfg.RIESGO_POR_OPERACION*100}%**")
    st.caption("Escaner de 7 Estrategias (Long & Short)")

with c2:
    st.markdown("### ⚙️ Filtros")
    solo_accion = st.checkbox("Ocultar 'Mantener'", value=True)

if st.button("🚀 INICIAR ESCANEO VISUAL"):
    
    st.markdown("---")
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()

    total_assets = len(cfg.TICKERS)
    conteo_oportunidades = 0
    
    for i, ticker in enumerate(cfg.TICKERS):
        status_text.text(f"Analizando {ticker} ({i+1}/{total_assets})...")
        
        try:
            # 1. Optimización
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            if winner and scout.data is not None and not scout.data.empty:
                df = scout.data.copy()
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # 2. Instanciar Estrategia Correcta
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
                
                # --- CLASIFICACIÓN INTELIGENTE ---
                
                # A) CASO LONG (COMPRA)
                if signal_val == 1:
                    is_new = (prev['Signal'] == 0)
                    
                    if "Golden Cross" in strat_name:
                        if is_new: 
                            tipo = "ENTRADA CRUCE DORADO"
                            direction = "LONG"
                            es_oportunidad_valida = True
                        else: tipo = "MANTENER TENDENCIA"
                            
                    elif "Bollinger" in strat_name:
                        if is_new:
                            tipo = "ENTRADA RUPTURA BB"
                            direction = "LONG"
                            es_oportunidad_valida = True
                        else: tipo = "MANTENER RUPTURA"

                    elif "EMA" in strat_name:
                        if is_new:
                            tipo = "ENTRADA EMA 8/21"
                            direction = "LONG"
                            es_oportunidad_valida = True
                        else: tipo = "MANTENER TENDENCIA EMA"

                    elif "Stochastic" in strat_name:
                        # Si K cruza D en zona baja (o simplemente empieza subida)
                        if is_new and today['Stoch_K'] < 40:
                            tipo = "ENTRADA STOCH SNIPER"
                            direction = "LONG"
                            es_oportunidad_valida = True
                        else: tipo = "MANTENER STOCH"

                    elif "Awesome" in strat_name:
                        if is_new:
                            tipo = "ENTRADA AWESOME (ZERO CROSS)"
                            direction = "LONG"
                            es_oportunidad_valida = True
                        else: tipo = "MANTENER AO"

                    elif "Mean Reversion" in strat_name:
                        tipo = "ENTRADA REBOTE RSI"
                        direction = "LONG"
                        es_oportunidad_valida = True 
                        
                    elif "MACD" in strat_name:
                        tipo = "ENTRADA MOMENTUM"
                        direction = "LONG"
                        es_oportunidad_valida = True

                # B) CASO SHORT (VENTA)
                elif signal_val == 0:
                    if "Mean Reversion" in strat_name and today['RSI'] > params['rsi_high']:
                        tipo = "ENTRADA SHORT (SOBRECOMPRA)"
                        direction = "SHORT"
                        es_oportunidad_valida = True
                    
                    elif "Golden Cross" in strat_name:
                        fast = df['Close'].rolling(params['fast']).mean()
                        slow = df['Close'].rolling(params['slow']).mean()
                        if fast.iloc[-1] < slow.iloc[-1] and fast.iloc[-2] >= slow.iloc[-2]:
                            tipo = "ENTRADA SHORT (CRUCE MUERTE)"
                            direction = "SHORT"
                            es_oportunidad_valida = True

                    elif "EMA" in strat_name:
                        ema_fast = df['Close'].ewm(span=params['fast'], adjust=False).mean()
                        ema_slow = df['Close'].ewm(span=params['slow'], adjust=False).mean()
                        if ema_fast.iloc[-1] < ema_slow.iloc[-1] and ema_fast.iloc[-2] >= ema_slow.iloc[-2]:
                            tipo = "ENTRADA SHORT (EMA CROSS)"
                            direction = "SHORT"
                            es_oportunidad_valida = True
                    
                    elif "Stochastic" in strat_name:
                         # Si K cruza D hacia abajo en zona alta
                         if today['Stoch_K'] < today['Stoch_D'] and today['Stoch_K'] > 70:
                             tipo = "ENTRADA SHORT (STOCH)"
                             direction = "SHORT"
                             es_oportunidad_valida = True

                # --- RENDERIZADO ---
                mostrar_tarjeta = False
                if solo_accion:
                    if es_oportunidad_valida: mostrar_tarjeta = True
                elif tipo != "NEUTRO": 
                    mostrar_tarjeta = True

                if mostrar_tarjeta:
                    conteo_oportunidades += 1
                    
                    # Cálculo de Riesgo
                    risk_mgr = RiskManager(df)
                    setup = risk_mgr.get_trade_setup(
                        entry_price=today['Close'], 
                        direction=direction if direction != "NONE" else "LONG", 
                        atr_multiplier=cfg.ATR_MULTIPLIER, 
                        risk_reward_ratio=cfg.RR_RATIO
                    )
                    
                    units = 0.0
                    inversion = 0.0
                    sl_txt, tp_txt = "-", "-"
                    
                    if setup and es_oportunidad_valida:
                        units = risk_mgr.calculate_position_size(
                            account_size=cfg.CAPITAL_TOTAL,
                            risk_pct_per_trade=cfg.RIESGO_POR_OPERACION,
                            trade_setup=setup
                        )
                        inversion = units * today['Close']
                        sl_txt = f"${setup['stop_loss']:.2f}"
                        tp_txt = f"${setup['take_profit']:.2f}"
                    
                    with results_container:
                        if direction == "LONG":
                            emoji = "🟢"
                            st.success(f"""
                            ### {emoji} {ticker} | {tipo}
                            **Estrategia:** {strat_name} | **Precio:** ${today['Close']:.2f}
                            
                            📦 **COMPRA:** `{units:.4f}` u. (${inversion:.2f})
                            🛡️ **Gestión:** Stop: `{sl_txt}` | Target: `{tp_txt}`
                            """)
                        elif direction == "SHORT":
                            emoji = "🔻"
                            st.error(f"""
                            ### {emoji} {ticker} | {tipo}
                            **Estrategia:** {strat_name} | **Precio:** ${today['Close']:.2f}
                            
                            📦 **VENTA (SHORT):** `{units:.4f}` u. (${inversion:.2f})
                            🛡️ **Gestión:** Stop: `{sl_txt}` | Target: `{tp_txt}`
                            """)
                        else:
                            st.info(f"🔵 **{ticker}**: {tipo}")

        except Exception as e:
            pass
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Auditoría completada.")
    progress_bar.empty()
    
    if conteo_oportunidades == 0:
        st.warning("No se encontraron señales activas bajo los filtros actuales.")
