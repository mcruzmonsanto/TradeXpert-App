# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import config as cfg
import requests

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="TradeXpert Dashboard", layout="wide", page_icon="📈")

# --- TÍTULO Y SIDEBAR ---
st.title("⚡ TradeXpert Pro: Centro de Mando")
st.markdown("---")

sidebar_ticker = st.sidebar.selectbox("Selecciona un Activo:", cfg.TICKERS)
st.sidebar.markdown(f"**Estrategia:** SMA {cfg.SMA_FAST}/{cfg.SMA_SLOW} + RSI < {cfg.RSI_THRESHOLD}")

# --- FUNCIÓN DE CARGA DE DATOS (CON CACHÉ PARA VELOCIDAD) ---
# app.py (Solo cambia la función get_data, el resto déjalo igual)

@st.cache_data(ttl=300) 
def get_data(symbol):
    try:
        # SIMPLIFICADO: Dejamos que yfinance maneje la sesión internamente
        # Al tener 'curl_cffi' instalado en requirements.txt, yfinance lo usará automágicamente.
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y")
        
        if df.empty: 
            st.warning(f"No se encontraron datos para {symbol}. Reintentando...")
            return None
        
        # Indicadores
        df['SMA_Fast'] = df['Close'].rolling(window=cfg.SMA_FAST).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=cfg.SMA_SLOW).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df

    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

# --- LÓGICA PRINCIPAL ---
df = get_data(sidebar_ticker)

if df is not None:
    # Obtener últimos valores
    today = df.iloc[-1]
    yesterday = df.iloc[-2]
    
    current_price = today['Close']
    rsi = today['RSI']
    trend = "ALCISTA 🐂" if today['SMA_Fast'] > today['SMA_Slow'] else "BAJISTA 🐻"
    
    # Lógica de Señal (Idéntica a tu bot)
    golden_cross = (yesterday['SMA_Fast'] < yesterday['SMA_Slow']) and (today['SMA_Fast'] > today['SMA_Slow'])
    death_cross = (yesterday['SMA_Fast'] > yesterday['SMA_Slow']) and (today['SMA_Fast'] < today['SMA_Slow'])
    
    signal = "MANTENER / ESPERAR"
    signal_color = "gray"
    
    if trend == "BAJISTA 🐻":
        signal = "NO OPERAR (CASH)"
        signal_color = "red"
    elif trend == "ALCISTA 🐂":
        if golden_cross and rsi < cfg.RSI_THRESHOLD:
            signal = "¡COMPRA FUERTE! 🚀"
            signal_color = "green"
        elif rsi > 70:
            signal = "SOBRECOMPRA (CUIDADO) ⚠️"
            signal_color = "orange"
        else:
            signal = "MANTENER TENDENCIA ✅"
            signal_color = "blue"
    
    if death_cross:
        signal = "VENTA (SALIDA) 🔻"
        signal_color = "red"

    # --- MOSTRAR MÉTRICAS (KPIs) ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Precio Actual", f"${current_price:.2f}", f"{today['Close'] - yesterday['Close']:.2f}")
    col2.metric("RSI (Fuerza)", f"{rsi:.2f}", delta=None)
    col3.metric("Tendencia", trend)
    
    # Semáforo Visual
    st.markdown(f"""
        <div style='background-color:{signal_color}; padding: 10px; border-radius: 5px; text-align: center; color: white;'>
            <h2 style='margin:0;'>SEÑAL: {signal}</h2>
        </div>
        """, unsafe_allow_html=True)

    # --- GRÁFICO INTERACTIVO (PLOTLY) ---
    st.subheader(f"Gráfico Técnico: {sidebar_ticker}")
    
    fig = go.Figure()
    
    # Velas
    fig.add_trace(go.Candlestick(x=df.index,
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'], name='Precio'))
    
    # Medias Móviles
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Fast'], line=dict(color='orange', width=1), name=f'SMA {cfg.SMA_FAST}'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Slow'], line=dict(color='green', width=2), name=f'SMA {cfg.SMA_SLOW}'))
    
    fig.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    # --- TABLA DE DATOS RECIENTES ---
    with st.expander("Ver últimos datos numéricos"):
        st.dataframe(df[['Close', 'SMA_Fast', 'SMA_Slow', 'RSI']].tail(10).sort_index(ascending=False))

else:
    st.error("No se pudieron cargar datos. Revisa tu conexión.")

# Botón para refrescar
if st.button('🔄 Actualizar Análisis'):
    st.cache_data.clear()

    st.rerun()

