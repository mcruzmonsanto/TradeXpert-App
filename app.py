# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import config as cfg
import sys

# Importamos nuestros módulos (Estrategias y Sentimiento)
sys.path.append('.') 
from strategies.mean_reversion import detect_bounce_play
from utils.news_sentiment import get_market_sentiment

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="TradeXpert IA", layout="wide", page_icon="🧠")
st.title("🧠 TradeXpert IA: Técnico + Fundamental")
st.markdown("---")

# Sidebar
sidebar_ticker = st.sidebar.selectbox("Selecciona Activo:", cfg.TICKERS)
st.sidebar.markdown("---")
st.sidebar.info("🤖 **IA Activada:**\nLeyendo noticias en tiempo real para filtrar entradas falsas.")

# --- FUNCIÓN DE DATOS ---
@st.cache_data(ttl=300)
def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y")
        if df.empty: return None
        
        # Indicadores
        df['SMA_Fast'] = df['Close'].rolling(window=cfg.SMA_FAST).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=cfg.SMA_SLOW).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    except Exception: return None

# --- CARGA DE DATOS ---
df = get_data(sidebar_ticker)

# --- ANÁLISIS DE SENTIMIENTO (IA) ---
# No usamos caché aquí porque las noticias cambian rápido
with st.spinner(f"Leyendo noticias sobre {sidebar_ticker}..."):
    sentiment_data = get_market_sentiment(sidebar_ticker)

if df is not None:
    today = df.iloc[-1]
    
    # Análisis Técnico
    trend = "ALCISTA 🐂" if today['SMA_Fast'] > today['SMA_Slow'] else "BAJISTA 🐻"
    analisis_rebote = detect_bounce_play(df, cfg.RSI_OVERSOLD)
    
    # --- FILTRO DE IA (SENTIMIENTO) ---
    # Si la estrategia de Rebote dice COMPRA, pero las noticias son MUY NEGATIVAS, la IA bloquea la señal.
    advertencia_ia = ""
    if "COMPRA" in analisis_rebote['signal'] or "OPORTUNIDAD" in analisis_rebote['signal']:
        if sentiment_data['score'] < -0.15: # Noticias muy malas
            analisis_rebote['signal'] = "BLOQUEADO POR IA 🛡️"
            analisis_rebote['color'] = "orange"
            analisis_rebote['reason'] = "Rebote técnico detectado, pero noticias muy negativas (Riesgo de caída)."
            advertencia_ia = "⚠️ **CUIDADO:** El análisis técnico sugiere compra, pero el fundamental es negativo."

    # --- VISUALIZACIÓN DE KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio", f"${today['Close']:.2f}", f"{today['Close'] - df.iloc[-2]['Close']:.2f}")
    c2.metric("RSI (Técnico)", f"{today['RSI']:.2f}")
    c3.metric("Sentimiento (IA)", sentiment_data['status'], delta=f"{sentiment_data['score']:.2f}")
    c4.markdown(f"**Decisión Final:**\n:{analisis_rebote['color']}[{analisis_rebote['signal']}]")

    if advertencia_ia:
        st.warning(advertencia_ia)

    st.markdown("---")
    
    # --- PANELES DE DETALLE ---
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader(f"📰 Noticias Recientes ({sidebar_ticker})")
        if sentiment_data['headlines']:
            for news in sentiment_data['headlines']:
                st.markdown(f"• [{news['title']}]({news['url']})")
        else:
            st.info("No se encontraron noticias recientes.")
            
    with col_der:
        st.subheader("💎 Análisis de Rebote")
        st.info(f"Razón: {analisis_rebote['reason']}")
        
    # --- GRÁFICO ---
    st.subheader("Gráfico Técnico")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Fast'], line=dict(color='orange', width=1), name='SMA 55'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Slow'], line=dict(color='blue', width=2), name='SMA 90'))
    
    # Marcadores de Rebote
    rebotes = df[df['RSI'] < cfg.RSI_OVERSOLD]
    fig.add_trace(go.Scatter(x=rebotes.index, y=rebotes['Close'], mode='markers', marker=dict(color='purple', size=8, symbol='diamond'), name='Zona Rebote'))

    fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Error cargando datos.")
    if st.button("Recargar"): st.rerun()