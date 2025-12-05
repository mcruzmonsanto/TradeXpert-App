# pages/radar.py
import streamlit as st
import pandas as pd
import sys

sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy
from classes.risk_manager import RiskManager
import config as cfg

st.set_page_config(page_title="Radar Pro V7", layout="wide", page_icon="📡")

c1, c2 = st.columns([3, 1])
with c1:
    st.title("📡 Radar Sniper Bidireccional")
    st.markdown(f"Capital: **${cfg.CAPITAL_TOTAL}** | Riesgo: **{cfg.RIESGO_POR_OPERACION*100}%**")
    st.caption("Filtro Inteligente: Muestra entradas nuevas y continuaciones válidas.")

with c2:
    st.markdown("### ⚙️ Filtros")
    solo_accion = st.checkbox("Ocultar 'Mantener Tendencia' (Ruido)", value=True)

if st.button("🚀 INICIAR ESCANEO"):
    
    oportunidades = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    live_results = st.container()

    total_assets = len(cfg.TICKERS)
    
    for i, ticker in enumerate(cfg.TICKERS):
        status_text.text(f"Analizando {ticker} ({i+1}/{total_assets})...")
        
        try:
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            if winner and scout.data is not None and not scout.data.empty:
                df = scout.data.copy()
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # Instanciar
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
                es_oportunidad_valida = False # Bandera clave
                
                # --- CLASIFICACIÓN INTELIGENTE ---
                
                # 1. CASO LONG (COMPRA)
                if signal_val == 1:
                    is_new = (prev['Signal'] == 0)
                    
                    if "Golden Cross" in strat_name:
                        # En Golden Cross, solo nos interesa la entrada exacta. Entrar tarde es riesgo.
                        if is_new: 
                            tipo = "🔔 ENTRADA LONG (CRUCE)"
                            direction = "LONG"
                            es_oportunidad_valida = True
                        else:
                            tipo = "MANTENER TENDENCIA"
                            
                    elif "Bollinger" in strat_name:
                        # Bollinger igual, la ruptura es el momento.
                        if is_new:
                            tipo = "🔔 ENTRADA LONG (RUPTURA)"
                            direction = "LONG"
                            es_oportunidad_valida = True
                        else:
                            tipo = "MANTENER RUPTURA"

                    elif "Mean Reversion" in strat_name:
                        # En Rebote, si sigue en zona baja, sigue siendo compra válida
                        tipo = "ENTRADA LONG (REBOTE)"
                        detalle = f"RSI {today['RSI']:.1f}"
                        direction = "LONG"
                        es_oportunidad_valida = True # Siempre mostramos rebotes activos
                        
                    elif "MACD" in strat_name:
                        # En MACD, el momentum dura. Es válido subirse.
                        tipo = "ENTRADA LONG (MOMENTUM)"
                        detalle = "Fuerza Alcista Activa"
                        direction = "LONG"
                        es_oportunidad_valida = True # Siempre mostramos momentum

                # 2. CASO SHORT (VENTA)
                elif signal_val == 0:
                    if "Mean Reversion" in strat_name and today['RSI'] > params['rsi_high']:
                        tipo = "🔻 ENTRADA SHORT (SOBRECOMPRA)"
                        detalle = f"RSI {today['RSI']:.1f}"
                        direction = "SHORT"
                        es_oportunidad_valida = True
                    
                    elif "Golden Cross" in strat_name:
                        fast = df['Close'].rolling(params['fast']).mean()
                        slow = df['Close'].rolling(params['slow']).mean()
                        if fast.iloc[-1] < slow.iloc[-1] and fast.iloc[-2] >= slow.iloc[-2]:
                            tipo = "🔻 ENTRADA SHORT (CRUCE MUERTE)"
                            direction = "SHORT"
                            es_oportunidad_valida = True

                    elif "MACD" in strat_name:
                        exp1 = df['Close'].ewm(span=params['fast'], adjust=False).mean()
                        exp2 = df['Close'].ewm(span=params['slow'], adjust=False).mean()
                        macd = exp1 - exp2
                        sig = macd.ewm(span=params['signal'], adjust=False).mean()
                        if macd.iloc[-1] < sig.iloc[-1] and macd.iloc[-2] >= sig.iloc[-2]:
                             tipo = "🔻 ENTRADA SHORT (MOMENTUM)"
                             direction = "SHORT"
                             es_oportunidad_valida = True

                # 3. GESTIÓN DE RIESGO
                trade_plan = None
                units = 0.0
                
                if es_oportunidad_valida:
                    risk_mgr = RiskManager(df)
                    setup = risk_mgr.get_trade_setup(
                        entry_price=today['Close'], 
                        direction=direction, 
                        atr_multiplier=cfg.ATR_MULTIPLIER, 
                        risk_reward_ratio=cfg.RR_RATIO
                    )
                    
                    if setup:
                        units = risk_mgr.calculate_position_size(
                            account_size=cfg.CAPITAL_TOTAL,
                            risk_pct_per_trade=cfg.RIESGO_POR_OPERACION,
                            trade_setup=setup
                        )
                        trade_plan = setup

                # 4. FILTRO FINAL
                mostrar = False
                if solo_accion:
                    # Mostramos solo si es una oportunidad válida (Nueva o Continua fuerte)
                    if es_oportunidad_valida: mostrar = True
                elif tipo != "NEUTRO": 
                    mostrar = True # Si el filtro está apagado, mostramos todo (incluido Mantener Tendencia)
                
                if mostrar:
                    item = {
                        "Ticker": ticker,
                        "Acción": tipo,
                        "Precio": f"${today['Close']:.2f}",
                        "Estrategia": strat_name,
                    }
                    
                    if trade_plan and units > 0:
                        item["Stop Loss"] = f"${trade_plan['stop_loss']:.2f}"
                        item["Take Profit"] = f"${trade_plan['take_profit']:.2f}"
                        item["Unidades"] = f"{units:.4f}"
                        
                        # Feedback visual
                        icon = "🟢" if direction == "LONG" else "🔻"
                        color = "green" if direction == "LONG" else "red"
                        
                        live_results.markdown(f":{color}[**{icon} {ticker}** {tipo}] -> Orden: {units:.4f} u.")
                    else:
                        color = "blue"
                        live_results.markdown(f":{color}[**{ticker}**: {tipo}]")
                        item["Stop Loss"] = "-"
                        item["Take Profit"] = "-"
                        item["Unidades"] = "-"

                    oportunidades.append(item)

        except Exception as e:
            # pass
            print(f"Error {ticker}: {e}")
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Auditoría completada.")
    progress_bar.empty()

    st.markdown("---")
    if oportunidades:
        st.subheader("📋 Plan de Trading Activo")
        df_ops = pd.DataFrame(oportunidades)
        
        def highlight_rows(val):
            if 'LONG' in val: return 'color: green; font-weight: bold'
            if 'SHORT' in val: return 'color: red; font-weight: bold'
            return 'color: gray'

        st.dataframe(df_ops.style.applymap(highlight_rows, subset=['Acción']), use_container_width=True)
    else:
        st.info("Sin oportunidades claras en este momento.")