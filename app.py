# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import config as cfg
import sys

# TRUCO: Permitir importar desde la carpeta strategies
sys.path.append('.') 
from strategies.mean_reversion import detect_bounce_play

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="TradeXpert Pro", layout="wide", page_icon="⚡")
st.title("⚡ TradeXpert Pro: Tablero Multi-Estrategia")
st.markdown("---")

# BARRA LATERAL
sidebar_ticker = st.sidebar.selectbox("Selecciona un Activo:", cfg.TICKERS)
st.sidebar.markdown("### 🧠 Estrategias Activas")
st.sidebar.info(f"1. **Tendencia (Golden Cross):**\nSMA {cfg.SMA_FAST} vs {cfg.SMA_SLOW}")
st.sidebar.info(f"2. **Rebote (Mean Reversion):**\nRSI < {cfg.RSI_OVERSOLD}")

# --- FUNCIÓN DE DATOS (BLINDADA) ---
@st.cache_data(ttl=300)
def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y")
        if df.empty: return None
        
        # CÁLCULOS TÉCNICOS
        df['SMA_Fast'] = df['Close'].rolling(window=cfg.SMA_FAST).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=cfg.SMA_SLOW).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    except Exception:
        return None

# --- MOTOR PRINCIPAL ---
df = get_data(sidebar_ticker)

if df is not None:
    today = df.iloc[-1]
    
    # ANÁLISIS 1: TENDENCIA (Tu Golden Cross)
    trend = "ALCISTA 🐂" if today['SMA_Fast'] > today['SMA_Slow'] else "BAJISTA 🐻"
    
    # ANÁLISIS 2: REBOTE (La nueva estrategia importada)
    analisis_rebote = detect_bounce_play(df, cfg.RSI_OVERSOLD)

    # --- MÉTRICAS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Precio Actual", f"${today['Close']:.2f}", f"{today['Close'] - df.iloc[-2]['Close']:.2f}")
    col2.metric("RSI", f"{today['RSI']:.2f}")
    col3.metric("Tendencia (Largo Plazo)", trend)
    col4.markdown(f"**Señal Corto Plazo:**\n:{analisis_rebote['color']}[{analisis_rebote['signal']}]")

    st.markdown("---")

    # --- SEMÁFOROS DE DECISIÓN ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔭 Inversión (Trend Following)")
        if trend == "ALCISTA 🐂" and today['RSI'] < 70:
            st.success("✅ MANTENER / COMPRAR")
        else:
            st.warning("⚠️ ESPERAR / PRECAUCIÓN")
            
    with c2:
        st.subheader("💎 Trading Rápido (Rebote)")
        if analisis_rebote['color'] == 'green':
            st.success(f"🚀 {analisis_rebote['reason']}")
        elif analisis_rebote['color'] == 'red':
            st.error(f"📉 {analisis_rebote['reason']}")
        else:
            st.info("😴 Sin oportunidad de rebote")

    # --- GRÁFICO ---
    st.subheader(f"Gráfico Técnico: {sidebar_ticker}")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Fast'], line=dict(color='orange', width=1), name='SMA Rápida'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Slow'], line=dict(color='blue', width=2), name='SMA Lenta'))
    
    # Marcar los puntos de rebote en el gráfico (Diamantes)
    rebotes = df[df['RSI'] < cfg.RSI_OVERSOLD]
    fig.add_trace(go.Scatter(x=rebotes.index, y=rebotes['Close'], mode='markers', 
                             marker=dict(color='purple', size=8, symbol='diamond'), name='Zona de Rebote'))

    fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Esperando datos... Si esto persiste, recarga la página.")
    if st.button("Recargar"): st.rerun()