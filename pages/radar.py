# pages/radar.py
import streamlit as st
import pandas as pd
import sys

# Importamos cerebro y riesgo
sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy
from classes.risk_manager import RiskManager
import config as cfg

st.set_page_config(page_title="Radar Sniper CFDs", layout="wide", page_icon="🎯")

c1, c2 = st.columns([3, 1])
with c1:
    st.title("🎯 Radar Sniper: Señales CFDs")
    st.markdown(f"Capital: **${cfg.CAPITAL_TOTAL}** | Riesgo: **{cfg.RIESGO_POR_OPERACION*100}%**")
    st.caption("Modo Fraccionario (CFD) activado: Cálculo de unidades exactas.")

with c2:
    st.markdown("### ⚙️ Filtros")
    solo_accion = st.checkbox("Solo Señales Activas", value=True)

if st.button("🚀 INICIAR ESCANEO SNIPER"):
    
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
                signal_val = today['Signal']
                
                tipo = "NEUTRO"
                detalle = ""
                is_buy = False
                
                # Lógica de detección (Simplificada)
                if signal_val == 1:
                    tipo = "MANTENER"
                    # Refinamos nombres para la acción
                    if "Mean Reversion" in strat_name: tipo = "COMPRA (REBOTE)"
                    elif "MACD" in strat_name: tipo = "COMPRA / MOMENTUM"
                    elif "Bollinger" in strat_name and df['Signal'].iloc[-2] == 0: tipo = "RUPTURA (ENTRADA)"
                    elif "Golden Cross" in strat_name and df['Signal'].iloc[-2] == 0: tipo = "CRUCE (ENTRADA)"
                    
                    if "COMPRA" in tipo or "ENTRADA" in tipo or "MOMENTUM" in tipo:
                        is_buy = True
                
                elif "Mean Reversion" in strat_name and today['RSI'] > params['rsi_high']:
                    tipo = "VENTA (TAKE PROFIT)"

                # GESTIÓN DE RIESGO
                trade_plan = None
                units_to_buy = 0.0
                
                if is_buy:
                    risk_mgr = RiskManager(df)
                    setup = risk_mgr.get_trade_setup(
                        entry_price=today['Close'], 
                        direction="LONG", 
                        atr_multiplier=cfg.ATR_MULTIPLIER, 
                        risk_reward_ratio=cfg.RR_RATIO
                    )
                    
                    if setup:
                        units_to_buy = risk_mgr.calculate_position_size(
                            account_size=cfg.CAPITAL_TOTAL,
                            risk_pct_per_trade=cfg.RIESGO_POR_OPERACION,
                            trade_setup=setup
                        )
                        trade_plan = setup

                # FILTRO
                mostrar = False
                if solo_accion:
                    if "COMPRA" in tipo or "VENTA" in tipo or "ENTRADA" in tipo or "MOMENTUM" in tipo: mostrar = True
                elif tipo != "NEUTRO": mostrar = True
                
                if mostrar:
                    item = {
                        "Ticker": ticker,
                        "Acción": tipo,
                        "Precio Entrada": f"${today['Close']:.2f}",
                        "Estrategia": strat_name,
                    }
                    
                    if trade_plan and units_to_buy > 0:
                        item["Stop Loss"] = f"${trade_plan['stop_loss']:.2f}"
                        item["Take Profit"] = f"${trade_plan['take_profit']:.2f}"
                        # AQUI ESTÁ EL CAMBIO VISUAL PARA CFDS:
                        item["Unidades"] = f"{units_to_buy:.4f}" 
                        
                        # Inversión estimada
                        inv_total = units_to_buy * today['Close']
                        item["Inversión Est."] = f"${inv_total:.2f}"

                        live_results.success(f"""
                        🟢 **{ticker}** | ENTRADA: ${today['Close']:.2f}
                        📦 **Orden:** Comprar **{units_to_buy:.4f}** unidades (Inversión: ${inv_total:.2f})
                        🛡️ SL: ${trade_plan['stop_loss']:.2f} | 🎯 TP: ${trade_plan['take_profit']:.2f}
                        """)
                    else:
                        color = "red" if "VENTA" in tipo else "blue"
                        live_results.markdown(f":{color}[**{ticker}**: {tipo}]")
                        item["Stop Loss"] = "-"
                        item["Take Profit"] = "-"
                        item["Unidades"] = "-"
                        item["Inversión Est."] = "-"

                    oportunidades.append(item)

        except Exception as e:
            # print(f"Error {ticker}: {e}")
            pass
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Auditoría completada.")
    progress_bar.empty()

    st.markdown("---")
    if oportunidades:
        st.subheader("📋 Plan de Trading (CFDs)")
        df_ops = pd.DataFrame(oportunidades)
        st.dataframe(df_ops, use_container_width=True)
    else:
        st.warning("Sin señales activas.")