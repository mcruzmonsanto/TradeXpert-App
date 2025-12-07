# pages/optimizador.py
import streamlit as st
import pandas as pd
import time
import sys
sys.path.append('.') 
from classes.scout import AssetScout
import config as cfg

st.set_page_config(page_title="IA Scout Pro", layout="wide", page_icon="🧠")
st.title("🧠 IA Scout: Auditoría de Riesgo y Retorno")

selected_tickers = st.sidebar.multiselect("Activos a Auditar:", cfg.TICKERS, default=cfg.TICKERS[:2])
start = st.sidebar.button("🚀 INICIAR AUDITORÍA")

if start:
    st.markdown("### 📡 Resultados del Análisis (5 Años - Velas 1D)")
    st.info("El sistema selecciona la estrategia con mayor retorno, siempre que el riesgo (Drawdown) sea aceptable.")
    
    for ticker in selected_tickers:
        scout = AssetScout(ticker)
        winner = scout.optimize()
        
        if winner:
            sharpe = winner['Sharpe']
            if sharpe > 1.0: 
                calidad = "EXCELENTE ⭐"
                color_sharpe = "green"
            elif sharpe > 0.5: 
                calidad = "BUENO ✅"
                color_sharpe = "blue"
            else: 
                calidad = "RIESGOSO ⚠️"
                color_sharpe = "orange"

            with st.container():
                # Icono según estrategia
                strat = winner['Estrategia']
                icon = "📈"
                if "Mean" in strat: icon = "💎"
                elif "EMA" in strat: icon = "🚀"
                elif "Stoch" in strat: icon = "🎯"
                elif "Awesome" in strat: icon = "🌊"

                st.markdown(f"#### {icon} {ticker} -> **{strat}**")
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Retorno Total", f"{winner['Retorno']*100:.2f}%")
                
                dd_val = winner['Drawdown']*100
                c2.metric("Max Drawdown", f"{dd_val:.2f}%", help="Riesgo máximo histórico")
                
                c3.metric("Sharpe Ratio", f"{sharpe:.2f}", delta=calidad)
                
                c4.code(f"{winner['Params']}")
                st.markdown("---")
            
            time.sleep(0.1)
