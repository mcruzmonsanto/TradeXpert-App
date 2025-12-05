# pages/radar.py
import streamlit as st
import pandas as pd
import sys

sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy
from classes.risk_manager import RiskManager
import config as cfg

st.set_page_config(page_title="Radar Bidireccional", layout="wide", page_icon="📡")

c1, c2 = st.columns([3, 1])
with c1:
    st.title("📡 Radar Bidireccional (Long & Short)")
    st.markdown(f"Capital: **${cfg.CAPITAL_TOTAL}** | Riesgo: **{cfg.RIESGO_POR_OPERACION*100}%**")
    st.caption("Detectando oportunidades de subida (Long) y bajada (Short).")

with c2:
    st.markdown("### ⚙️ Filtros")
    solo_accion = st.checkbox("Solo Señales Activas", value=True)

if st.button("🚀 INICIAR ESCANEO TOTAL"):
    
    oportunidades = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    live_results = st.container()

    total_assets = len(cfg.TICKERS)
    
    for i, ticker in enumerate(cfg.TICKERS):
        status_text.text(f"Auditando {ticker} ({i+1}/{total_assets})...")
        
        try:
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            if winner and scout.data is not None and not scout.data.empty:
                df = scout.data.copy()
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # Instanciar estrategia
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
                detalle = ""
                direction = "NONE" # LONG o SHORT
                
                # --- LÓGICA DE DETECCIÓN AVANZADA ---
                
                # 1. CASO LONG (COMPRA) - Señal = 1
                if signal_val == 1:
                    if prev['Signal'] == 0: # Entrada Fresca
                        tipo = "ENTRADA LONG (ALCISTA)"
                        direction = "LONG"
                        if "Mean Reversion" in strat_name: detalle = f"Rebote (RSI {today['RSI']:.1f})"
                        elif "Golden Cross" in strat_name: detalle = "Cruce Dorado"
                        elif "MACD" in strat_name: detalle = "Cruce MACD > Signal"
                    else:
                        tipo = "MANTENER LONG"
                
                # 2. CASO SHORT (VENTA EN CORTO) - Señal = 0 (o específica)
                # Como nuestras estrategias devuelven 0 para "No Long", inferimos el Short
                # buscando la condición inversa explícita.
                
                elif signal_val == 0:
                    
                    # A) Mean Reversion: RSI > High -> SHORT
                    if "Mean Reversion" in strat_name and today['RSI'] > params['rsi_high']:
                        tipo = "ENTRADA SHORT (BAJISTA)"
                        direction = "SHORT"
                        detalle = f"Sobrecompra Extrema (RSI {today['RSI']:.1f})"
                    
                    # B) Golden Cross: Cruce de la Muerte (Rapida < Lenta HOY y ayer no)
                    elif "Golden Cross" in strat_name:
                        fast = df['Close'].rolling(params['fast']).mean()
                        slow = df['Close'].rolling(params['slow']).mean()
                        if fast.iloc[-1] < slow.iloc[-1] and fast.iloc[-2] >= slow.iloc[-2]:
                            tipo = "ENTRADA SHORT (DEATH CROSS)"
                            direction = "SHORT"
                            detalle = "Cambio de Tendencia a Bajista"

                    # C) MACD: Cruce hacia abajo
                    elif "MACD" in strat_name:
                        exp1 = df['Close'].ewm(span=params['fast'], adjust=False).mean()
                        exp2 = df['Close'].ewm(span=params['slow'], adjust=False).mean()
                        macd = exp1 - exp2
                        sig = macd.ewm(span=params['signal'], adjust=False).mean()
                        if macd.iloc[-1] < sig.iloc[-1] and macd.iloc[-2] >= sig.iloc[-2]:
                             tipo = "ENTRADA SHORT (MOMENTUM)"
                             direction = "SHORT"
                             detalle = "MACD cruza hacia abajo"

                # 3. CÁLCULO DE RIESGO
                trade_plan = None
                units_to_trade = 0.0
                
                # Solo calculamos riesgo si hay una ENTRADA nueva (Long o Short)
                if "ENTRADA" in tipo:
                    risk_mgr = RiskManager(df)
                    setup = risk_mgr.get_trade_setup(
                        entry_price=today['Close'], 
                        direction=direction, # Pasamos LONG o SHORT
                        atr_multiplier=cfg.ATR_MULTIPLIER, 
                        risk_reward_ratio=cfg.RR_RATIO
                    )
                    
                    if setup:
                        units_to_trade = risk_mgr.calculate_position_size(
                            account_size=cfg.CAPITAL_TOTAL,
                            risk_pct_per_trade=cfg.RIESGO_POR_OPERACION,
                            trade_setup=setup
                        )
                        trade_plan = setup

                # 4. FILTRADO
                mostrar = False
                if solo_accion:
                    if "ENTRADA" in tipo: mostrar = True
                elif tipo != "NEUTRO": mostrar = True
                
                if mostrar:
                    item = {
                        "Ticker": ticker,
                        "Acción": tipo,
                        "Precio": f"${today['Close']:.2f}",
                        "Estrategia": strat_name,
                    }
                    
                    if trade_plan and units_to_trade > 0:
                        item["Stop Loss"] = f"${trade_plan['stop_loss']:.2f}"
                        item["Take Profit"] = f"${trade_plan['take_profit']:.2f}"
                        item["Unidades"] = f"{units_to_trade:.4f}"
                        
                        costo = units_to_trade * today['Close']
                        item["Valor Posición"] = f"${costo:.2f}"

                        # Icono y Color según dirección
                        icono = "🟢" if direction == "LONG" else "🔻"
                        
                        live_results.success(f"""
                        {icono} **{ticker}** | {tipo} @ ${today['Close']:.2f}
                        📦 **Orden:** {direction} {units_to_trade:.4f} unidades
                        🛡️ SL: ${trade_plan['stop_loss']:.2f} | 🎯 TP: ${trade_plan['take_profit']:.2f}
                        """)
                    else:
                        color = "blue"
                        live_results.markdown(f":{color}[**{ticker}**: {tipo}]")
                        item["Stop Loss"] = "-"
                        item["Take Profit"] = "-"
                        item["Unidades"] = "-"
                        item["Valor Posición"] = "-"

                    oportunidades.append(item)

        except Exception as e:
             # pass
             print(f"Error {ticker}: {e}")
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Auditoría Bidireccional Completa.")
    progress_bar.empty()

    st.markdown("---")
    if oportunidades:
        st.subheader("📋 Plan de Trading (Long & Short)")
        df_ops = pd.DataFrame(oportunidades)
        
        # Colorear filas
        def highlight_rows(val):
            if 'LONG' in val: return 'color: green; font-weight: bold'
            if 'SHORT' in val: return 'color: red; font-weight: bold'
            return 'color: gray'

        st.dataframe(df_ops.style.applymap(highlight_rows, subset=['Acción']), use_container_width=True)
    else:
        st.info("Sin oportunidades de entrada (ni Long ni Short) en este momento.")