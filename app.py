# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys

# Importamos el cerebro OOP
sys.path.append('.') 
from classes.scout import AssetScout
import config as cfg

st.set_page_config(page_title="TradeXpert Auto-Pilot", layout="wide", page_icon="⚡")

st.title("⚡ TradeXpert: Piloto Automático")
st.markdown("El sistema detecta y aplica la mejor estrategia matemática para el activo seleccionado.")
st.markdown("---")

# 1. SIDEBAR
ticker = st.sidebar.selectbox("Selecciona Activo:", cfg.TICKERS)

# 2. CEREBRO: OPTIMIZACIÓN EN TIEMPO REAL
# Usamos caché para que si cambias de activo y vuelves, no recalcule
@st.cache_data(ttl=3600) # Guarda la optimización por 1 hora
def get_best_strategy(symbol):
    scout = AssetScout(symbol)
    winner = scout.optimize() # Esto prueba las 4 estrategias y devuelve la mejor
    return winner, scout.data # Devolvemos también los datos descargados

# Ejecutamos el análisis (Puede tardar 3-5 segundos la primera vez)
with st.spinner(f"🤖 La IA está auditando {ticker} para encontrar su mejor estrategia..."):
    winner, df = get_best_strategy(ticker)

if winner and df is not None:
    # Datos del último día
    today = df.iloc[-1]
    last_price = today['Close']
    prev_price = df.iloc[-2]['Close']
    
    # Extraemos la info ganadora
    strat_name = winner['Estrategia']
    params = winner['Params']
    retorno_5y = winner['Retorno'] * 100
    sharpe = winner['Sharpe']
    
    # --- ENCABEZADO DE INTELIGENCIA ---
    st.success(f"✅ Estrategia Óptima Detectada: **{strat_name}**")
    
    # Métricas clave
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio Actual", f"${last_price:.2f}", f"{last_price - prev_price:.2f}")
    c2.metric("Retorno Histórico (5y)", f"{retorno_5y:.0f}%")
    c3.metric("Sharpe Ratio", f"{sharpe:.2f}")
    c4.code(f"Config: {params}")

    st.markdown("---")

    # --- GENERADOR DE SEÑALES EN TIEMPO REAL ---
    # Ahora instanciamos la estrategia ganadora para ver qué dice HOY
    from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy

    # Seleccionamos la clase correcta según el nombre
    strat_obj = None
    if "Golden Cross" in strat_name:
        strat_obj = GoldenCrossStrategy()
    elif "Mean Reversion" in strat_name:
        strat_obj = MeanReversionStrategy()
    elif "Bollinger" in strat_name:
        strat_obj = BollingerBreakoutStrategy()
    elif "MACD" in strat_name:
        strat_obj = MACDStrategy()

    # Ejecutamos la estrategia con los MEJORES PARÁMETROS encontrados
    # Esto añade la columna 'Signal' al dataframe
    metrics = strat_obj.backtest(df, params) 
    # (Nota: backtest() ya genera las señales internamente en 'df' modificado, 
    # pero necesitamos acceder al df con señales. Pequeño ajuste necesario en strategies.py si quisiéramos ser puristas, 
    # pero para visualizar rápido, recalculamos las columnas visuales abajo).
    
    # Recalculamos indicadores visuales para el gráfico según la estrategia
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'))

    # VISUALIZACIÓN DINÁMICA
    signal_today = "NEUTRO"
    color_signal = "gray"
    
    if "Golden Cross" in strat_name:
        fast_sma = df['Close'].rolling(params['fast']).mean()
        slow_sma = df['Close'].rolling(params['slow']).mean()
        fig.add_trace(go.Scatter(x=df.index, y=fast_sma, line=dict(color='orange'), name=f"SMA {params['fast']}"))
        fig.add_trace(go.Scatter(x=df.index, y=slow_sma, line=dict(color='blue'), name=f"SMA {params['slow']}"))
        
        # Señal
        if fast_sma.iloc[-1] > slow_sma.iloc[-1]:
            signal_today = "MANTENER / COMPRAR (Tendencia)"
            color_signal = "green"
        else:
            signal_today = "VENDER / ESPERAR"
            color_signal = "red"

    elif "Mean Reversion" in strat_name:
        # RSI ya calculado en backtest, lo recalculamos para mostrar
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        c1.metric("Nivel RSI", f"{current_rsi:.2f}")
        
        if current_rsi < params['rsi_low']:
            signal_today = "¡COMPRA POR PÁNICO! 💎"
            color_signal = "green"
        elif current_rsi > params['rsi_high']:
            signal_today = "VENTA POR RECUPERACIÓN"
            color_signal = "red"
        else:
            signal_today = "ESPERAR"

    elif "Bollinger" in strat_name:
        mid = df['Close'].rolling(params['window']).mean()
        std = df['Close'].rolling(params['window']).std()
        upper = mid + (std * params['std_dev'])
        lower = mid - (std * params['std_dev'])
        
        fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='gray', dash='dot'), name="Banda Sup"))
        fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='gray', dash='dot'), name="Banda Inf"))
        
        if last_price > upper.iloc[-1]:
            signal_today = "RUPTURA ALCISTA (MOMENTUM) 🚀"
            color_signal = "green"
        elif last_price < mid.iloc[-1]:
            signal_today = "NEUTRO / BAJISTA"
            color_signal = "gray"
            
    elif "MACD" in strat_name:
        # MACD Chart es complejo de pintar sobre el precio, mostramos señal textual
        exp1 = df['Close'].ewm(span=params['fast'], adjust=False).mean()
        exp2 = df['Close'].ewm(span=params['slow'], adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=params['signal'], adjust=False).mean()
        
        if macd.iloc[-1] > signal_line.iloc[-1]:
            signal_today = "MOMENTUM POSITIVO (COMPRA) 🟢"
            color_signal = "green"
        else:
            signal_today = "MOMENTUM NEGATIVO (VENTA) 🔴"
            color_signal = "red"

    # --- MOSTRAR LA DECISIÓN GIGANTE ---
    st.markdown(f"""
    <div style='background-color:{color_signal}; padding: 15px; border-radius: 10px; text-align: center; color: white; margin-bottom: 20px;'>
        <h2 style='margin:0;'>SEÑAL HOY: {signal_today}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Gráfico
    st.subheader(f"Gráfico Técnico: {ticker}")
    fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("No se pudieron cargar datos o realizar la optimización.")