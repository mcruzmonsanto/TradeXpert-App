# pages/radar.py
import streamlit as st
import pandas as pd
import time
import sys
import plotly.graph_objects as go

# Importamos el cerebro
sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy
import config as cfg

st.set_page_config(page_title="Radar de Oportunidades", layout="wide", page_icon="📡")

st.title("📡 Radar de Oportunidades: Escaneo Masivo")
st.markdown("""
Este módulo audita **todo tu universo de activos** (Acciones, Crypto, ETFs), selecciona la mejor estrategia para cada uno 
y te muestra **SOLO** aquellos que tienen señales de entrada o salida hoy.
""")

# Botón de Inicio
if st.button("🚀 INICIAR ESCANEO GLOBAL"):
    
    oportunidades = []
    
    # Barra de Progreso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Contenedor para mostrar hallazgos en tiempo real
    live_results = st.container()

    # --- BUCLE DE ESCANEO ---
    total_assets = len(cfg.TICKERS)
    
    for i, ticker in enumerate(cfg.TICKERS):
        status_text.text(f"Auditando {ticker} ({i+1}/{total_assets})...")
        
        try:
            # 1. Optimización (Encontrar la mejor estrategia)
            # Usamos el Scout pero sin caché persistente para asegurar datos frescos de hoy
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            if winner and scout.data is not None and not scout.data.empty:
                df = scout.data
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # 2. Instanciar la estrategia ganadora
                strat_obj = None
                if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
                elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
                elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
                elif "MACD" in strat_name: strat_obj = MACDStrategy()
                
                # 3. Ejecutar Backtest Rápido para obtener señal de HOY
                # Esto añade la columna 'Signal' al dataframe
                _ = strat_obj.backtest(df, params)
                
                # 4. Decodificar Señal de Hoy
                today_signal_val = df['Signal'].iloc[-1]
                prev_signal_val = df['Signal'].iloc[-2] # Para detectar cambios frescos
                
                signal_text = "NEUTRO"
                tipo = "ESPERAR"
                
                # Lógica específica por estrategia para traducir el 1/0 a texto
                if "Mean Reversion" in strat_name:
                    rsi = df['RSI'].iloc[-1]
                    if rsi < params['rsi_low']:
                        signal_text = f"COMPRA (RSI {rsi:.1f})"
                        tipo = "COMPRA"
                    elif rsi > params['rsi_high']:
                        signal_text = "VENTA (Sobrecompra)"
                        tipo = "VENTA"
                
                elif "Golden Cross" in strat_name:
                    # Si Signal es 1 hoy y era 0 hace poco, es entrada nueva
                    if today_signal_val == 1: signal_text = "MANTENER TENDENCIA"
                    # Refinamiento: ¿Hubo cruce HOY?
                    fast = df['Close'].rolling(params['fast']).mean()
                    slow = df['Close'].rolling(params['slow']).mean()
                    if fast.iloc[-1] > slow.iloc[-1] and fast.iloc[-2] <= slow.iloc[-2]:
                        signal_text = "¡CRUCE ALCISTA HOY!"
                        tipo = "COMPRA"
                    elif today_signal_val == 1:
                        tipo = "MANTENER"

                elif "Bollinger" in strat_name:
                    close = df['Close'].iloc[-1]
                    # Recalcular bandas rápido para verificar
                    mid = df['Close'].rolling(params['window']).mean()
                    std = df['Close'].rolling(params['window']).std()
                    upper = mid + (std * params['std_dev'])
                    
                    if close > upper.iloc[-1]:
                        signal_text = "RUPTURA ALCISTA"
                        tipo = "COMPRA"
                    elif today_signal_val == 1: # Ya estaba dentro
                         tipo = "MANTENER"

                elif "MACD" in strat_name:
                    exp1 = df['Close'].ewm(span=params['fast'], adjust=False).mean()
                    exp2 = df['Close'].ewm(span=params['slow'], adjust=False).mean()
                    macd = exp1 - exp2
                    sig = macd.ewm(span=params['signal'], adjust=False).mean()
                    
                    if macd.iloc[-1] > sig.iloc[-1] and macd.iloc[-2] <= sig.iloc[-2]:
                         signal_text = "CRUCE MACD (ENTRADA)"
                         tipo = "COMPRA"
                    elif macd.iloc[-1] > sig.iloc[-1]:
                         signal_text = "MOMENTUM POSITIVO"
                         tipo = "MANTENER"
                    else:
                        tipo = "ESPERAR"

                # 5. FILTRO: Solo guardamos si es COMPRA o VENTA (Ignoramos Mantener/Esperar para limpiar ruido)
                # Opcional: Si quieres ver todo, quita el if. Pero el usuario pidió "Alertas".
                if tipo in ["COMPRA", "VENTA"]:
                    oportunidades.append({
                        "Ticker": ticker,
                        "Acción": tipo,
                        "Estrategia": strat_name,
                        "Detalle": signal_text,
                        "Precio": f"${df['Close'].iloc[-1]:.2f}",
                        "Sharpe": f"{winner['Sharpe']:.2f}"
                    })
                    
                    # Mostrar hallazgo en tiempo real
                    color = "green" if tipo == "COMPRA" else "red"
                    live_results.markdown(f":{color}[**DETECTADO: {ticker} -> {tipo} ({signal_text})**]")

        except Exception as e:
            print(f"Error en {ticker}: {e}")
            
        # Actualizar barra
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Escaneo Finalizado.")
    progress_bar.empty()

    # --- MOSTRAR RESULTADOS FINALES ---
    st.markdown("---")
    st.subheader("📋 Tablero de Alertas Activas")
    
    if oportunidades:
        df_ops = pd.DataFrame(oportunidades)
        
        # Estilizar tabla
        def color_action(val):
            color = 'green' if val == 'COMPRA' else 'red'
            return f'color: {color}; font-weight: bold'
            
        st.dataframe(df_ops.style.applymap(color_action, subset=['Acción']), use_container_width=True)
        
        st.success(f"🎯 Se encontraron {len(oportunidades)} oportunidades de trading para hoy.")
        st.info("Ve al menú 'Auto-Pilot' y selecciona el activo para ver el gráfico detallado.")
        
    else:
        st.info("😴 El mercado está tranquilo hoy. Ninguna estrategia dio señal de entrada/salida nueva.")