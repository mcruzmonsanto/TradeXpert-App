# pages/simulador.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import sys

# Truco para importar config desde la carpeta superior
sys.path.append('.') 
import config as cfg

st.set_page_config(page_title="Laboratorio de Backtest", layout="wide", page_icon="🔬")

st.title("🔬 Laboratorio: Prueba de Estrategias")
st.markdown("Aquí sometemos las ideas a la prueba de fuego con datos históricos.")

# --- BARRA LATERAL ---
ticker = st.sidebar.selectbox("Elige Activo para Testear:", cfg.TICKERS)
capital_inicial = st.sidebar.number_input("Capital Inicial ($)", value=1000)

# Selector de Estrategia
estrategia = st.sidebar.radio("Estrategia a Auditar:", 
                              ["Reversión a la Media (Rebote)", "Golden Cross (Tendencia)"])

# --- MOTOR DE BACKTEST ---
@st.cache_data(ttl=600)
def backtest_engine(symbol, strategy_name):
    # Descargamos 5 años para tener buena data
    df = yf.Ticker(symbol).history(period="5y")
    
    if df.empty: return None, None
    
    # Cálculos necesarios
    df['SMA_55'] = df['Close'].rolling(window=55).mean()
    df['SMA_90'] = df['Close'].rolling(window=90).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Variables de Simulación
    capital = capital_inicial
    posicion = 0 # 0 = Cash, >0 = Acciones
    historial = []
    trades = [] # Para guardar cada operación
    
    precio_compra = 0
    
    for i in range(50, len(df)):
        fecha = df.index[i]
        precio = df['Close'].iloc[i]
        rsi = df['RSI'].iloc[i]
        sma_fast = df['SMA_55'].iloc[i]
        sma_slow = df['SMA_90'].iloc[i]
        
        # --- LÓGICA DE LA ESTRATEGIA 1: REBOTE (RSI < 30) ---
        if strategy_name == "Reversión a la Media (Rebote)":
            # COMPRA: Pánico extremo (RSI < 30) y tenemos Cash
            if posicion == 0 and rsi < 30:
                posicion = capital / precio
                capital = 0
                precio_compra = precio
                trades.append({'Fecha': fecha, 'Tipo': 'COMPRA', 'Precio': precio})
            
            # VENTA: Retorno a la normalidad (RSI > 50) o Stop Loss de emergencia (10%)
            elif posicion > 0:
                stop_loss = precio < (precio_compra * 0.90) # 10% Stop
                take_profit = rsi > 50                      # Salida técnica
                
                if take_profit or stop_loss:
                    razon = "Take Profit (RSI>50)" if take_profit else "STOP LOSS"
                    capital = posicion * precio
                    posicion = 0
                    trades.append({'Fecha': fecha, 'Tipo': 'VENTA', 'Precio': precio, 'Razón': razon})

        # --- LÓGICA DE LA ESTRATEGIA 2: TENDENCIA (Golden Cross) ---
        elif strategy_name == "Golden Cross (Tendencia)":
            cruce_alcista = df['SMA_55'].iloc[i-1] < df['SMA_90'].iloc[i-1] and sma_fast > sma_slow
            cruce_bajista = df['SMA_55'].iloc[i-1] > df['SMA_90'].iloc[i-1] and sma_fast < sma_slow
            
            if posicion == 0 and cruce_alcista:
                posicion = capital / precio
                capital = 0
                trades.append({'Fecha': fecha, 'Tipo': 'COMPRA', 'Precio': precio})
            
            elif posicion > 0 and cruce_bajista:
                capital = posicion * precio
                posicion = 0
                trades.append({'Fecha': fecha, 'Tipo': 'VENTA', 'Precio': precio, 'Razón': 'Cruce Muerte'})

        # Registro diario del valor del portafolio
        valor_actual = capital if posicion == 0 else posicion * precio
        historial.append(valor_actual)
        
    # Crear DataFrame de resultados
    df_res = pd.DataFrame(historial, index=df.index[50:], columns=['Equity'])
    return df_res, pd.DataFrame(trades)

# --- EJECUCIÓN ---
if st.button(f"🚀 Simular {estrategia} en {ticker}"):
    with st.spinner("Viajando al pasado para probar tu estrategia..."):
        df_equity, df_trades = backtest_engine(ticker, estrategia)
    
    if df_equity is not None:
        # MÉTRICAS FINALES
        capital_final = df_equity['Equity'].iloc[-1]
        retorno = ((capital_final - capital_inicial) / capital_inicial) * 100
        
        # Mostrar KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Final", f"${capital_final:.2f}")
        c2.metric("Retorno Total", f"{retorno:.2f}%", delta_color="normal")
        c3.metric("Operaciones Totales", len(df_trades))
        
        # GRÁFICO DE CRECIMIENTO
        st.subheader("Curva de Crecimiento de Capital")
        st.line_chart(df_equity)
        
        # TABLA DE TRADES
        with st.expander("Ver detalle de cada Compra/Venta"):
            if not df_trades.empty:
                st.dataframe(df_trades)
            else:
                st.warning("No hubo operaciones con estos parámetros.")
                
        # ANÁLISIS DEL MENTOR
        st.info(f"""
        ℹ️ **Nota del Mentor sobre {estrategia}:**
        - Si ves una línea que sube y baja bruscamente, es una estrategia volátil.
        - En 'Reversión a la Media', fíjate si el **Stop Loss** te salvó de caídas grandes.
        - Compara el resultado con simplemente comprar y mantener.
        """)