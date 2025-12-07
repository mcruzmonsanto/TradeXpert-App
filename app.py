import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys

sys.path.append('.') 
from classes.scout import AssetScout
# Importar TODO para que funcione la visualización
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)
from classes.strategies_pro import SuperTrendStrategy, SqueezeMomentumStrategy, ADXStrategy
import config as cfg

st.set_page_config(page_title="TradeXpert Auto-Pilot", layout="wide", page_icon="⚡")

st.title("⚡ TradeXpert: Piloto Automático")
ticker = st.sidebar.selectbox("Selecciona Activo:", cfg.TICKERS)

@st.cache_data(ttl=3600)
def get_best_strategy(symbol):
    scout = AssetScout(symbol)
    winner = scout.optimize() 
    return winner, scout.data

with st.spinner(f"🤖 Auditando {ticker}..."):
    winner, df = get_best_strategy(ticker)

if winner and df is not None:
    today = df.iloc[-1]
    strat_name = winner['Estrategia']
    params = winner['Params']
    
    st.success(f"✅ Estrategia Óptima: **{strat_name}**")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio", f"${today['Close']:.2f}")
    c2.metric("Retorno 2y", f"{winner['Retorno']*100:.0f}%")
    c3.metric("Sharpe", f"{winner['Sharpe']:.2f}")
    c4.code(f"{params}")
    st.markdown("---")

    # INSTANCIAR
    strat_obj = None
    if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
    elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
    elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
    elif "MACD" in strat_name: strat_obj = MACDStrategy()
    elif "EMA" in strat_name: strat_obj = EMAStrategy()
    elif "Stochastic" in strat_name: strat_obj = StochRSIStrategy()
    elif "Awesome" in strat_name: strat_obj = AwesomeOscillatorStrategy()
    elif "SuperTrend" in strat_name: strat_obj = SuperTrendStrategy()
    elif "Squeeze" in strat_name: strat_obj = SqueezeMomentumStrategy()
    elif "ADX" in strat_name: strat_obj = ADXStrategy()

    df = strat_obj.generate_signals(df, params)
    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'))

    signal_today = "NEUTRO"
    color_signal = "gray"
    
    # VISUALIZACIÓN PRO
    if "SuperTrend" in strat_name:
        fig.add_trace(go.Scatter(x=df.index, y=df['SuperTrend'], line=dict(color='purple', width=2), name="SuperTrend Line"))
        if df['Trend_Dir'].iloc[-1] == 1:
            signal_today, color_signal = "TENDENCIA ALCISTA (SUPER)", "green"
        else:
            signal_today, color_signal = "TENDENCIA BAJISTA", "red"

    elif "Squeeze" in strat_name:
        # Pinta simple el momentum
        mom = df['Momentum'].iloc[-1]
        st.metric("Momentum", f"{mom:.2f}")
        if mom > 0: signal_today, color_signal = "MOMENTUM POSITIVO", "green"
        else: signal_today, color_signal = "MOMENTUM NEGATIVO", "red"

    elif "ADX" in strat_name:
        adx = df['ADX'].iloc[-1]
        st.metric("ADX (Fuerza)", f"{adx:.2f}")
        if df['Signal'].iloc[-1] == 1: signal_today, color_signal = "TENDENCIA FUERTE ALCISTA", "green"
        else: signal_today, color_signal = "RANGO / NEUTRO", "gray"

    # VISUALIZACIÓN CLÁSICA (Resumida para que quepa)
    elif "EMA" in strat_name:
        f = df['Close'].ewm(span=params['fast'], adjust=False).mean()
        s = df['Close'].ewm(span=params['slow'], adjust=False).mean()
        fig.add_trace(go.Scatter(x=df.index, y=f, line=dict(color='cyan'), name="Fast"))
        fig.add_trace(go.Scatter(x=df.index, y=s, line=dict(color='purple'), name="Slow"))
        if f.iloc[-1] > s.iloc[-1]: signal_today, color_signal = "ALCISTA", "green"
        else: signal_today, color_signal = "BAJISTA", "red"
        
    elif "Golden" in strat_name:
        if df['Signal'].iloc[-1] == 1: signal_today, color_signal = "ALCISTA", "green"
        else: signal_today, color_signal = "BAJISTA", "red"

    elif "Mean" in strat_name:
        st.metric("RSI", f"{today['RSI']:.2f}")
        if today['RSI'] < params['rsi_low']: signal_today, color_signal = "COMPRA REBOTE", "green"
        elif today['RSI'] > params['rsi_high']: signal_today, color_signal = "VENTA", "red"

    st.markdown(f"<div style='background-color:{color_signal}; padding: 10px; border-radius: 5px; text-align: center; color: white;'><h3>{signal_today}</h3></div>", unsafe_allow_html=True)
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Error cargando datos.")
