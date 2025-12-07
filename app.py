# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys

# Importamos el cerebro OOP
sys.path.append('.') 
from classes.scout import AssetScout
# Importamos TODAS las estrategias para poder instanciarlas
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)
import config as cfg

st.set_page_config(page_title="TradeXpert Auto-Pilot", layout="wide", page_icon="⚡")

st.title("⚡ TradeXpert: Piloto Automático")
st.markdown("El sistema detecta y aplica la mejor estrategia matemática para el activo seleccionado.")
st.markdown("---")

# 1. SIDEBAR
ticker = st.sidebar.selectbox("Selecciona Activo:", cfg.TICKERS)

# 2. CEREBRO: OPTIMIZACIÓN EN TIEMPO REAL
@st.cache_data(ttl=3600)
def get_best_strategy(symbol):
    scout = AssetScout(symbol)
    winner = scout.optimize() 
    return winner, scout.data

with st.spinner(f"🤖 La IA está auditando {ticker} con las 7 estrategias..."):
    winner, df = get_best_strategy(ticker)

if winner and df is not None:
    # Datos recientes
    today = df.iloc[-1]
    last_price = today['Close']
    prev_price = df.iloc[-2]['Close']
    
    strat_name = winner['Estrategia']
    params = winner['Params']
    retorno_5y = winner['Retorno'] * 100
    sharpe = winner['Sharpe']
    
    # --- ENCABEZADO ---
    st.success(f"✅ Estrategia Óptima Detectada: **{strat_name}**")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio Actual", f"${last_price:.2f}", f"{last_price - prev_price:.2f}")
    c2.metric("Retorno Histórico (5y)", f"{retorno_5y:.0f}%")
    c3.metric("Sharpe Ratio", f"{sharpe:.2f}")
    c4.code(f"Config: {params}")

    st.markdown("---")

    # --- INSTANCIAR ESTRATEGIA GANADORA ---
    strat_obj = None
    if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
    elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
    elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
    elif "MACD" in strat_name: strat_obj = MACDStrategy()
    elif "EMA" in strat_name: strat_obj = EMAStrategy()
    elif "Stochastic" in strat_name: strat_obj = StochRSIStrategy()
    elif "Awesome" in strat_name: strat_obj = AwesomeOscillatorStrategy()

    # Ejecutar lógica para obtener señales visuales
    df = strat_obj.generate_signals(df, params)
    
    # --- VISUALIZACIÓN DINÁMICA ---
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'))

    signal_today = "NEUTRO"
    color_signal = "gray"
    
    # Lógica de visualización específica por estrategia
    if "Golden Cross" in strat_name:
        fast_sma = df['Close'].rolling(params['fast']).mean()
        slow_sma = df['Close'].rolling(params['slow']).mean()
        fig.add_trace(go.Scatter(x=df.index, y=fast_sma, line=dict(color='orange'), name=f"SMA {params['fast']}"))
        fig.add_trace(go.Scatter(x=df.index, y=slow_sma, line=dict(color='blue'), name=f"SMA {params['slow']}"))
        
        if fast_sma.iloc[-1] > slow_sma.iloc[-1]:
            signal_today = "MANTENER TENDENCIA (ALCISTA)"
            color_signal = "green"
        else:
            signal_today = "TENDENCIA BAJISTA"
            color_signal = "red"

    elif "EMA" in strat_name:
        ema_fast = df['Close'].ewm(span=params['fast'], adjust=False).mean()
        ema_slow = df['Close'].ewm(span=params['slow'], adjust=False).mean()
        fig.add_trace(go.Scatter(x=df.index, y=ema_fast, line=dict(color='cyan', width=1), name=f"EMA {params['fast']}"))
        fig.add_trace(go.Scatter(x=df.index, y=ema_slow, line=dict(color='purple', width=1), name=f"EMA {params['slow']}"))
        
        if ema_fast.iloc[-1] > ema_slow.iloc[-1]:
            signal_today = "MOMENTUM ALCISTA (EMA)"
            color_signal = "green"
        else:
            signal_today = "MOMENTUM BAJISTA (EMA)"
            color_signal = "red"

    elif "Mean Reversion" in strat_name:
        # Mostramos RSI como métrica
        current_rsi = today['RSI']
        st.metric("Nivel RSI Actual", f"{current_rsi:.2f}")
        
        if current_rsi < params['rsi_low']:
            signal_today = "¡COMPRA POR PÁNICO! 💎"
            color_signal = "green"
        elif current_rsi > params['rsi_high']:
            signal_today = "VENTA (SOBRECOMPRA)"
            color_signal = "red"
        else:
            signal_today = "ESPERAR"

    elif "Bollinger" in strat_name:
        mid = df['Close'].rolling(params['window']).mean()
        std = df['Close'].rolling(params['window']).std()
        upper = mid + (std * params['std_dev'])
        lower = mid - (std * params['std_dev'])
        
        fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='gray', dash='dot'), name="Upper Band"))
        fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='gray', dash='dot'), name="Lower Band"))
        
        if last_price > upper.iloc[-1]:
            signal_today = "RUPTURA ALCISTA 🚀"
            color_signal = "green"
        elif df['Signal'].iloc[-1] == 1:
            signal_today = "MANTENER RUPTURA"
            color_signal = "green"
        else:
            signal_today = "DENTRO DE BANDAS (NEUTRO)"
            
    elif "MACD" in strat_name:
        # MACD es difícil de pintar sobre precio, usamos texto claro
        exp1 = df['Close'].ewm(span=params['fast'], adjust=False).mean()
        exp2 = df['Close'].ewm(span=params['slow'], adjust=False).mean()
        macd = exp1 - exp2
        sig = macd.ewm(span=params['signal'], adjust=False).mean()
        
        val_macd = macd.iloc[-1]
        val_sig = sig.iloc[-1]
        
        st.metric("Valor MACD", f"{val_macd:.3f}", delta=f"{val_macd - val_sig:.3f}")
        
        if val_macd > val_sig:
            signal_today = "MOMENTUM POSITIVO"
            color_signal = "green"
        else:
            signal_today = "MOMENTUM NEGATIVO"
            color_signal = "red"

    elif "Stochastic" in strat_name:
        k = today['Stoch_K']
        d = today['Stoch_D']
        st.metric("Stoch K / D", f"{k:.1f} / {d:.1f}")
        
        if k > d and k < 80:
            signal_today = "TENDENCIA STOCH POSITIVA"
            color_signal = "green"
        elif k < d:
            signal_today = "CRUCE BAJISTA STOCH"
            color_signal = "red"
        else:
            signal_today = "NEUTRO"

    elif "Awesome" in strat_name:
        ao = today['AO']
        st.metric("Awesome Oscillator", f"{ao:.3f}", delta_color="normal")
        
        if ao > 0:
            signal_today = "AO POSITIVO (ALCISTA)"
            color_signal = "green"
        else:
            signal_today = "AO NEGATIVO (BAJISTA)"
            color_signal = "red"

    # --- MOSTRAR DECISIÓN ---
    st.markdown(f"""
    <div style='background-color:{color_signal}; padding: 15px; border-radius: 10px; text-align: center; color: white; margin-bottom: 20px;'>
        <h2 style='margin:0;'>SEÑAL HOY: {signal_today}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader(f"Gráfico Técnico: {ticker}")
    fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("No se pudieron cargar datos o realizar la optimización.")
