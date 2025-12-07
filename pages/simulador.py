# pages/simulador.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import sys

sys.path.append('.') 
from classes.scout import AssetScout
# Importamos las clases para poder simularlas manualmente
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)
import config as cfg

st.set_page_config(page_title="Laboratorio de Backtest", layout="wide", page_icon="🔬")

st.title("🔬 Laboratorio: Simulador Manual")
st.markdown("Prueba cómo hubiera funcionado cualquiera de las 7 estrategias en un activo específico.")

# --- SIDEBAR ---
ticker = st.sidebar.selectbox("Elige Activo:", cfg.TICKERS)

opciones_estrategia = [
    "Golden Cross (Trend)", 
    "RSI Mean Reversion", 
    "Bollinger Breakout",
    "MACD Momentum",
    "EMA 8/21 Crossover",
    "Stochastic RSI",
    "Awesome Oscillator"
]
estrategia_nombre = st.sidebar.selectbox("Elige Estrategia:", opciones_estrategia)

# --- LÓGICA DE SIMULACIÓN ---
if st.button(f"🚀 Simular {estrategia_nombre} en {ticker}"):
    
    # 1. Descargar datos frescos
    with st.spinner("Descargando historial de 5 años..."):
        df = yf.Ticker(ticker).history(period="5y")
    
    if df.empty:
        st.error("No hay datos disponibles.")
    else:
        # 2. Instanciar la clase seleccionada
        strat_obj = None
        # Mapeo de nombres a clases
        if "Golden" in estrategia_nombre: strat_obj = GoldenCrossStrategy()
        elif "Mean" in estrategia_nombre: strat_obj = MeanReversionStrategy()
        elif "Bollinger" in estrategia_nombre: strat_obj = BollingerBreakoutStrategy()
        elif "MACD" in estrategia_nombre: strat_obj = MACDStrategy()
        elif "EMA" in estrategia_nombre: strat_obj = EMAStrategy()
        elif "Stochastic" in estrategia_nombre: strat_obj = StochRSIStrategy()
        elif "Awesome" in estrategia_nombre: strat_obj = AwesomeOscillatorStrategy()

        # 3. Encontrar los MEJORES parámetros para ESTA estrategia específica
        # (Usamos el Scout pero "hackeado" para optimizar solo la estrategia elegida)
        with st.spinner(f"Optimizando parámetros para {estrategia_nombre}..."):
            
            # Instanciamos un Scout temporal
            temp_scout = AssetScout(ticker)
            # Sobreescribimos su lista de estrategias para que SOLO tenga la que elegimos
            temp_scout.strategies = [strat_obj]
            # Ejecutamos optimización (probará configs solo para esta estrategia)
            winner = temp_scout.optimize()
            
            best_params = winner['Params']
            
        # 4. Correr Backtest final con esos parámetros
        metrics = strat_obj.backtest(df, best_params)
        
        # --- MOSTRAR RESULTADOS ---
        st.success(f"Mejor configuración encontrada: `{best_params}`")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Retorno Total", f"{metrics['return']*100:.2f}%")
        c2.metric("Max Drawdown", f"{metrics['drawdown']*100:.2f}%")
        c3.metric("Sharpe Ratio", f"{metrics['sharpe']:.2f}")
        
        # Gráfico de Curva de Capital (Equity Curve)
        st.subheader("Curva de Crecimiento de Capital")
        st.line_chart(metrics['equity_curve'])
        
        st.info("ℹ️ Este gráfico muestra cómo hubiera crecido $1 dólar invertido con esta estrategia.")
