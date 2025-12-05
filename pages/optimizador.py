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

# Sidebar
selected_tickers = st.sidebar.multiselect("Activos:", cfg.TICKERS, default=cfg.TICKERS[:2])
start = st.sidebar.button("🚀 INICIAR AUDITORÍA")

if start:
    st.markdown("### 📡 Resultados del Análisis (5 Años - Velas 1D)")
    
    for ticker in selected_tickers:
        scout = AssetScout(ticker)
        winner = scout.optimize()
        
        if winner:
            # Lógica de colores según Sharpe Ratio
            sharpe = winner['Sharpe']
            if sharpe > 1.0: 
                calidad = "EXCELENTE ⭐"
                border_color = "green"
            elif sharpe > 0.5: 
                calidad = "BUENO ✅"
                border_color = "blue"
            else: 
                calidad = "RIESGOSO ⚠️"
                border_color = "orange"

            with st.container():
                st.markdown(f"#### 📊 {ticker} -> {winner['Estrategia']}")
                
                # Columnas de Métricas
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Retorno Total", f"{winner['Retorno']*100:.2f}%")
                c2.metric("Max Drawdown", f"{winner['Drawdown']*100:.2f}%", help="La caída máxima desde el pico más alto.")
                c3.metric("Sharpe Ratio", f"{sharpe:.2f}", help=">1 es excelente. Mide retorno vs riesgo.")
                c4.metric("Calidad", calidad)
                
                st.caption(f"⚙️ Configuración Óptima: `{winner['Params']}`")
                st.markdown("---")
            
            time.sleep(0.1)