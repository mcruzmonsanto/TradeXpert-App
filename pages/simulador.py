# pages/simulador.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import sys

sys.path.append('.') 
from classes.scout import AssetScout
# Importamos las clases para reconstruir la historia del ganador
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy
)
import config as cfg

st.set_page_config(page_title="Simulador Automático", layout="wide", page_icon="🏆")

st.title("🏆 Simulador: Torneo de Estrategias")
st.markdown("""
Olvídate de probar manualmente. Este módulo enfrenta a **todas tus estrategias** entre sí 
usando datos históricos de 5 años y te entrega automáticamente la **Mejor Configuración** matemática.
""")

# --- SIDEBAR ---
st.sidebar.header("Configuración")
ticker = st.sidebar.selectbox("Selecciona el Activo a Optimizar:", cfg.TICKERS)
capital_inicial = st.sidebar.number_input("Capital Inicial ($)", value=1000)

if st.sidebar.button(f"🚀 BUSCAR MEJOR ESTRATEGIA PARA {ticker}"):
    
    # 1. El Scout hace el trabajo sucio (Prueba las 7 estrategias x N parámetros)
    with st.spinner(f"⚡ La IA está simulando miles de días de trading para {ticker}..."):
        scout = AssetScout(ticker)
        winner = scout.optimize() # Devuelve el diccionario del ganador
        df_data = scout.data      # Los datos históricos descargados

    if winner and not df_data.empty:
        # Extraemos los datos del campeón
        strat_name = winner['Estrategia']
        best_params = winner['Params']
        
        st.canvas = st.container()
        
        # --- ENCABEZADO DEL GANADOR ---
        st.success(f"🎉 ¡Tenemos un Ganador! La mejor estrategia para **{ticker}** es: **{strat_name}**")
        
        # Métricas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Retorno Total (5 Años)", f"{winner['Retorno']*100:.2f}%")
        c2.metric("Capital Final", f"${capital_inicial * (1 + winner['Retorno']):,.2f}")
        c3.metric("Sharpe Ratio", f"{winner['Sharpe']:.2f}", help="Calidad del retorno. >1 es bueno.")
        c4.metric("Max Drawdown", f"{winner['Drawdown']*100:.2f}%", help="Peor caída soportada.")
        
        st.markdown(f"**⚙️ Configuración Maestra:** `{best_params}`")
        st.markdown("---")

        # --- RECONSTRUCCIÓN VISUAL ---
        # El Scout nos dice QUIEN ganó, pero para graficar la curva día a día,
        # necesitamos volver a ejecutar esa estrategia específica con los parámetros ganadores.
        
        strat_obj = None
        if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
        elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
        elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
        elif "MACD" in strat_name: strat_obj = MACDStrategy()
        elif "EMA" in strat_name: strat_obj = EMAStrategy()
        elif "Stochastic" in strat_name: strat_obj = StochRSIStrategy()
        elif "Awesome" in strat_name: strat_obj = AwesomeOscillatorStrategy()
        
        # Corremos el backtest detallado solo del ganador
        detailed_metrics = strat_obj.backtest(df_data, best_params)
        equity_curve = detailed_metrics['equity_curve'] * capital_inicial # Escalamos al capital
        
        # --- GRÁFICO DE CURVA DE CAPITAL ---
        st.subheader(f"📈 Crecimiento de tu Inversión ({strat_name})")
        
        # Crear gráfico bonito con Plotly
        fig = go.Figure()
        
        # Línea de Equity
        fig.add_trace(go.Scatter(
            x=equity_curve.index, 
            y=equity_curve.values, 
            mode='lines', 
            name='Portafolio',
            line=dict(color='#00FF00', width=2),
            fill='tozeroy', # Relleno bonito bajo la curva
            fillcolor='rgba(0, 255, 0, 0.1)'
        ))
        
        # Línea base (Buy & Hold) para comparar
        buy_hold = (df_data['Close'] / df_data['Close'].iloc[0]) * capital_inicial
        fig.add_trace(go.Scatter(
            x=buy_hold.index, 
            y=buy_hold.values, 
            mode='lines', 
            name='Buy & Hold (Referencia)',
            line=dict(color='gray', width=1, dash='dot')
        ))

        fig.update_layout(
            template="plotly_dark",
            title=f"Rendimiento vs Buy & Hold",
            xaxis_title="Fecha",
            yaxis_title="Capital ($)",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # --- ANÁLISIS DEL MENTOR ---
        st.info(f"""
        🧠 **Análisis Automático:**
        El algoritmo probó todas las estrategias disponibles. La **{strat_name}** superó a las demás porque se adaptó mejor a la personalidad de **{ticker}**.
        
        * **¿Qué significa esto?** Que para operar {ticker} hoy, deberías usar las señales de esta estrategia específica y ignorar las demás.
        * **¿Siguiente paso?** Ve al 'Radar' o 'Auto-Pilot'. El sistema ya sabe esto y te dará las señales basadas en este resultado.
        """)

    else:
        st.error("No se encontraron resultados. Intenta con otro activo.")
