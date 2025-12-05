# pages/radar.py
import streamlit as st
import pandas as pd
import sys

# Importamos el cerebro
sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy
import config as cfg

st.set_page_config(page_title="Radar Pro V3", layout="wide", page_icon="📡")

st.title("📡 Radar de Oportunidades: Escaneo Masivo V3")
st.markdown("Auditoría en tiempo real. **Versión Corregida con Inyección de Señales.**")

if st.button("🚀 INICIAR ESCANEO GLOBAL"):
    
    oportunidades = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    live_results = st.container()

    total_assets = len(cfg.TICKERS)
    
    for i, ticker in enumerate(cfg.TICKERS):
        status_text.text(f"Auditando {ticker} ({i+1}/{total_assets})...")
        
        try:
            # 1. Optimización (Scout busca la mejor estrategia)
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            # Verificamos que haya datos y un ganador
            if winner and scout.data is not None and not scout.data.empty:
                df = scout.data.copy() # Trabajamos sobre una copia local segura
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # 2. Instanciar estrategia ganadora
                strat_obj = None
                if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
                elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
                elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
                elif "MACD" in strat_name: strat_obj = MACDStrategy()
                
                # --- CORRECCIÓN CRÍTICA AQUÍ ---
                # Forzamos la generación de la columna 'Signal' en ESTE dataframe
                df = strat_obj.generate_signals(df, params)
                # -------------------------------
                
                # 3. Análisis de la Señal de HOY
                today = df.iloc[-1]
                
                # Protección: Si la estrategia falló en crear 'Signal', la creamos en 0
                if 'Signal' not in df.columns:
                    df['Signal'] = 0

                signal_val = today['Signal'] # 1 (Activo) o 0 (Inactivo)
                
                tipo = "NEUTRO"
                detalle = ""
                
                # A) LÓGICA DE DETECCIÓN DE COMPRA/MANTENER
                if signal_val == 1:
                    # Por defecto es mantener, pero afinamos el texto
                    tipo = "MANTENER TENDENCIA" 
                    
                    if "Mean Reversion" in strat_name:
                        tipo = "COMPRA (REBOTE)"
                        detalle = f"RSI en zona baja ({today['RSI']:.1f})"
                    elif "Golden Cross" in strat_name:
                        detalle = f"Tendencia Alcista Activa"
                    elif "Bollinger" in strat_name:
                        detalle = f"Precio sobre Banda Superior"
                    elif "MACD" in strat_name:
                        # Si es MACD, el Auto-Pilot decía COMPRA, así que aquí también
                        tipo = "COMPRA / MOMENTUM" 
                        detalle = "MACD > Signal Line"

                    # Detección de entrada FRESCA (Cruce hoy)
                    # Si ayer era 0 y hoy es 1, es una entrada nueva (¡Prioridad!)
                    if df['Signal'].iloc[-2] == 0:
                        tipo = "🔔 ¡ENTRADA NUEVA HOY!"

                # B) LÓGICA DE VENTA (Solo para Mean Reversion por ahora)
                elif "Mean Reversion" in strat_name:
                    if today['RSI'] > params['rsi_high']:
                        tipo = "VENTA (TAKE PROFIT)"
                        detalle = f"Sobrecompra RSI {today['RSI']:.1f}"

                # 4. GUARDAR RESULTADO
                # Guardamos todo lo que NO sea NEUTRO
                if tipo != "NEUTRO":
                    oportunidades.append({
                        "Ticker": ticker,
                        "Estrategia": strat_name,
                        "Acción": tipo,
                        "Detalle": detalle,
                        "Precio": f"${today['Close']:.2f}",
                        "Sharpe": f"{winner['Sharpe']:.2f}"
                    })
                    
                    # Mostrar en vivo (Feedback visual)
                    icon = "🟢" if "COMPRA" in tipo or "ENTRADA" in tipo else "🔵" if "MANTENER" in tipo else "🔴"
                    live_results.markdown(f"{icon} **{ticker}**: {tipo} ({strat_name})")

        except Exception as e:
            # Mostrar el error en pantalla para depurar si vuelve a pasar
            st.error(f"Error procesando {ticker}: {e}")
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Escaneo Finalizado.")
    progress_bar.empty()

    # --- TABLA FINAL ---
    st.markdown("---")
    if oportunidades:
        st.subheader(f"📋 Resultados: {len(oportunidades)} Señales Encontradas")
        df_ops = pd.DataFrame(oportunidades)
        
        def color_highlight(val):
            if 'ENTRADA' in val or 'COMPRA' in val: return 'color: green; font-weight: bold'
            if 'VENTA' in val: return 'color: red; font-weight: bold'
            return 'color: blue'
            
        st.dataframe(df_ops.style.applymap(color_highlight, subset=['Acción']), use_container_width=True)
    else:
        st.warning("El escáner funcionó correctamente, pero no encontró señales activas bajo los parámetros actuales.")