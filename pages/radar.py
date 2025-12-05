# pages/radar.py
import streamlit as st
import pandas as pd
import sys

# Importamos cerebro y riesgo
sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy
from classes.risk_manager import RiskManager # <--- NUEVO
import config as cfg

st.set_page_config(page_title="Radar Sniper V5", layout="wide", page_icon="🎯")

c1, c2 = st.columns([3, 1])
with c1:
    st.title("🎯 Radar Sniper: Señales + Gestión de Riesgo")
    st.markdown(f"Capital Base: **${cfg.CAPITAL_TOTAL}** | Riesgo por Trade: **{cfg.RIESGO_POR_OPERACION*100}%**")
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
            # 1. Scout
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            if winner and scout.data is not None and not scout.data.empty:
                df = scout.data.copy()
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # 2. Estrategia
                strat_obj = None
                if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
                elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
                elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
                elif "MACD" in strat_name: strat_obj = MACDStrategy()
                
                df = strat_obj.generate_signals(df, params)
                if 'Signal' not in df.columns: df['Signal'] = 0
                
                today = df.iloc[-1]
                signal_val = today['Signal']
                
                # 3. Clasificación
                tipo = "NEUTRO"
                detalle = ""
                
                # Detectar COMPRA/MOMENTUM
                if signal_val == 1:
                    tipo = "MANTENER"
                    if "Mean Reversion" in strat_name: tipo = "COMPRA (REBOTE)"
                    elif "MACD" in strat_name: tipo = "COMPRA / MOMENTUM"
                    elif "Bollinger" in strat_name and df['Signal'].iloc[-2] == 0: tipo = "RUPTURA (ENTRADA)"
                    elif "Golden Cross" in strat_name and df['Signal'].iloc[-2] == 0: tipo = "CRUCE (ENTRADA)"
                    
                    if "COMPRA" in tipo or "ENTRADA" in tipo or "MOMENTUM" in tipo:
                        is_buy = True
                    else:
                        is_buy = False # Es solo Mantener
                
                elif "Mean Reversion" in strat_name and today['RSI'] > params['rsi_high']:
                    tipo = "VENTA (TAKE PROFIT)"
                    is_buy = False
                else:
                    is_buy = False

                # 4. GESTIÓN DE RIESGO (Solo si es Compra/Entrada)
                trade_plan = None
                shares_to_buy = 0
                
                if is_buy:
                    risk_mgr = RiskManager(df)
                    # Calculamos niveles
                    setup = risk_mgr.get_trade_setup(
                        entry_price=today['Close'], 
                        direction="LONG", 
                        atr_multiplier=cfg.ATR_MULTIPLIER, 
                        risk_reward_ratio=cfg.RR_RATIO
                    )
                    
                    if setup:
                        # Calculamos tamaño de posición
                        shares_to_buy = risk_mgr.calculate_position_size(
                            account_size=cfg.CAPITAL_TOTAL,
                            risk_pct_per_trade=cfg.RIESGO_POR_OPERACION,
                            trade_setup=setup
                        )
                        trade_plan = setup

                # 5. FILTRADO Y GUARDADO
                mostrar = False
                if solo_accion:
                    if "COMPRA" in tipo or "VENTA" in tipo or "ENTRADA" in tipo or "MOMENTUM" in tipo: mostrar = True
                elif tipo != "NEUTRO": mostrar = True
                
                if mostrar:
                    item = {
                        "Ticker": ticker,
                        "Acción": tipo,
                        "Precio": f"${today['Close']:.2f}",
                        "Estrategia": strat_name,
                    }
                    
                    # Si hay plan de trading, agregamos los datos ricos
                    if trade_plan and shares_to_buy > 0:
                        item["Stop Loss"] = f"${trade_plan['stop_loss']:.2f}"
                        item["Take Profit"] = f"${trade_plan['take_profit']:.2f}"
                        item["Cantidad"] = f"{shares_to_buy} accs"
                        item["R/R"] = f"1:{cfg.RR_RATIO}"
                        
                        # Mensaje en vivo detallado
                        live_results.success(f"""
                        🟢 **{ticker}** | ENTRADA: ${today['Close']:.2f}
                        🎯 Objetivo: ${trade_plan['take_profit']:.2f} | 🛡️ Stop: ${trade_plan['stop_loss']:.2f}
                        📦 **COMPRAR: {shares_to_buy} acciones** (Riesgo controlado)
                        """)
                    else:
                        # Si es venta o mantener, mostramos simple
                        color = "red" if "VENTA" in tipo else "blue"
                        live_results.markdown(f":{color}[**{ticker}**: {tipo}]")
                        item["Stop Loss"] = "-"
                        item["Take Profit"] = "-"
                        item["Cantidad"] = "-"
                        item["R/R"] = "-"

                    oportunidades.append(item)

        except Exception as e:
            # pass
            print(f"Error {ticker}: {e}")
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Cálculo de Riesgo Completado.")
    progress_bar.empty()

    # --- TABLA FINAL ---
    st.markdown("---")
    if oportunidades:
        st.subheader("📋 Plan de Ejecución Profesional")
        df_ops = pd.DataFrame(oportunidades)
        st.dataframe(df_ops, use_container_width=True)
        
        st.info("💡 **Nota:** La 'Cantidad' está calculada para que, si el precio toca el Stop Loss, solo pierdas el 2% de tu capital ($200 USD).")
    else:
        st.warning("Sin oportunidades claras ahora.")