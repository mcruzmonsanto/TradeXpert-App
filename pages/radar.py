# pages/radar.py
import streamlit as st
import pandas as pd
import sys

sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy
from classes.risk_manager import RiskManager
import config as cfg

st.set_page_config(page_title="Radar Visual Pro", layout="wide", page_icon="📡")

# --- ENCABEZADO ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("📡 Radar Visual: Plan de Trading")
    st.markdown(f"Capital: **${cfg.CAPITAL_TOTAL}** | Riesgo: **{cfg.RIESGO_POR_OPERACION*100}%**")
    st.caption("Tarjetas de Ejecución para CFDs (Long & Short)")

with c2:
    st.markdown("### ⚙️ Filtros")
    solo_accion = st.checkbox("Ocultar 'Mantener'", value=True)

if st.button("🚀 INICIAR ESCANEO VISUAL"):
    
    st.markdown("---")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Contenedor principal donde irán apareciendo las tarjetas
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
                
                # 2. Instanciar
                strat_obj = None
                if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
                elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
                elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
                elif "MACD" in strat_name: strat_obj = MACDStrategy()
                
                df = strat_obj.generate_signals(df, params)
                if 'Signal' not in df.columns: df['Signal'] = 0
                
                today = df.iloc[-1]
                prev = df.iloc[-2]
                signal_val = today['Signal']
                
                tipo = "NEUTRO"
                direction = "NONE"
                es_oportunidad_valida = False
                
                # --- CLASIFICACIÓN INTELIGENTE (Lógica V7) ---
                
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
                            tipo = "ENTRADA RUPTURA"
                            direction = "LONG"
                            es_oportunidad_valida = True
                        else: tipo = "MANTENER RUPTURA"

                    elif "Mean Reversion" in strat_name:
                        tipo = "ENTRADA REBOTE"
                        direction = "LONG"
                        es_oportunidad_valida = True # Siempre mostramos rebotes activos
                        
                    elif "MACD" in strat_name:
                        tipo = "ENTRADA MOMENTUM"
                        direction = "LONG"
                        es_oportunidad_valida = True # Siempre mostramos momentum

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

                    elif "MACD" in strat_name:
                        exp1 = df['Close'].ewm(span=params['fast'], adjust=False).mean()
                        exp2 = df['Close'].ewm(span=params['slow'], adjust=False).mean()
                        macd = exp1 - exp2
                        sig = macd.ewm(span=params['signal'], adjust=False).mean()
                        if macd.iloc[-1] < sig.iloc[-1] and macd.iloc[-2] >= sig.iloc[-2]:
                             tipo = "ENTRADA SHORT (MOMENTUM)"
                             direction = "SHORT"
                             es_oportunidad_valida = True

                # --- FILTRO VISUAL ---
                mostrar_tarjeta = False
                if solo_accion:
                    if es_oportunidad_valida: mostrar_tarjeta = True
                elif tipo != "NEUTRO": 
                    mostrar_tarjeta = True

                # --- RENDERIZADO DE TARJETA ---
                if mostrar_tarjeta:
                    conteo_oportunidades += 1
                    
                    # Cálculos de Riesgo
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
                    
                    # DISEÑO DE LA TARJETA
                    with results_container:
                        # Color de fondo según dirección
                        if direction == "LONG":
                            emoji = "🟢"
                            st.success(f"""
                            ### {emoji} {ticker} | {tipo}
                            **Estrategia:** {strat_name} | **Precio:** ${today['Close']:.2f}
                            
                            📦 **ORDEN DE COMPRA:**
                            * **Unidades:** `{units:.4f}`
                            * **Inversión:** `${inversion:.2f}`
                            
                            🛡️ **Gestión:** Stop Loss: `{sl_txt}` | Take Profit: `{tp_txt}`
                            """)
                        elif direction == "SHORT":
                            emoji = "🔻"
                            st.error(f"""
                            ### {emoji} {ticker} | {tipo}
                            **Estrategia:** {strat_name} | **Precio:** ${today['Close']:.2f}
                            
                            📦 **ORDEN DE VENTA (SHORT):**
                            * **Unidades:** `{units:.4f}`
                            * **Inversión:** `${inversion:.2f}`
                            
                            🛡️ **Gestión:** Stop Loss: `{sl_txt}` | Take Profit: `{tp_txt}`
                            """)
                        else:
                            # Para "Mantener" (Azul)
                            st.info(f"🔵 **{ticker}**: {tipo} (Estrategia: {strat_name})")

        except Exception as e:
            pass # Ignorar errores puntuales para no ensuciar
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Auditoría completada.")
    progress_bar.empty()
    
    if conteo_oportunidades == 0:
        st.warning("No se encontraron señales activas bajo los filtros actuales.")