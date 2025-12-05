# pages/radar.py
import streamlit as st
import pandas as pd
import sys

# Importamos el cerebro
sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy
import config as cfg

st.set_page_config(page_title="Radar Pro V4", layout="wide", page_icon="📡")

# --- ENCABEZADO Y FILTROS ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("📡 Radar de Oportunidades")
    st.markdown("Auditoría en tiempo real. **Detectando señales accionables.**")

with c2:
    st.markdown("### ⚙️ Filtros")
    # POR DEFECTO: True (Solo queremos ver acción)
    solo_accion = st.checkbox("Mostrar SOLO Señales de Entrada/Salida", value=True)

if st.button("🚀 INICIAR ESCANEO GLOBAL"):
    
    oportunidades = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    live_results = st.container()

    total_assets = len(cfg.TICKERS)
    
    for i, ticker in enumerate(cfg.TICKERS):
        status_text.text(f"Auditando {ticker} ({i+1}/{total_assets})...")
        
        try:
            # 1. Optimización
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            if winner and scout.data is not None and not scout.data.empty:
                # TRABAJAMOS CON COPIA SEGURA
                df = scout.data.copy()
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # 2. Instanciar estrategia
                strat_obj = None
                if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
                elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
                elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
                elif "MACD" in strat_name: strat_obj = MACDStrategy()
                
                # 3. Generar Señales (INYECCIÓN EXPLÍCITA)
                df = strat_obj.generate_signals(df, params)
                
                # 4. Análisis de HOY
                if 'Signal' not in df.columns: df['Signal'] = 0
                
                today = df.iloc[-1]
                signal_val = today['Signal']
                
                tipo = "NEUTRO"
                detalle = ""
                
                # --- CLASIFICACIÓN DE SEÑALES ---
                
                # A) Lógica de COMPRA / MANTENER
                if signal_val == 1:
                    tipo = "MANTENER TENDENCIA" # Base
                    
                    if "Mean Reversion" in strat_name:
                        tipo = "COMPRA (REBOTE)"
                        detalle = f"RSI {today['RSI']:.1f}"
                    elif "MACD" in strat_name:
                        # MACD suele ser una señal de momentum continuo, lo dejamos como compra/acción
                        tipo = "COMPRA / MOMENTUM"
                        detalle = "MACD > Signal"
                    elif "Bollinger" in strat_name:
                        detalle = "Sobre Banda Sup"
                    elif "Golden Cross" in strat_name:
                        detalle = f"Tendencia Alcista"

                    # Detección de ENTRADA FRESCA (Cruce hoy)
                    # Si ayer era 0 y hoy es 1, es la señal más importante
                    if df['Signal'].iloc[-2] == 0:
                        tipo = "🔔 ¡ENTRADA NUEVA HOY!"

                # B) Lógica de VENTA (Mean Reversion)
                elif "Mean Reversion" in strat_name:
                    if today['RSI'] > params['rsi_high']:
                        tipo = "VENTA (TAKE PROFIT)"
                        detalle = f"Sobrecompra {today['RSI']:.1f}"

                # --- 5. FILTRO INTELIGENTE (TU PETICIÓN) ---
                agregar = False
                
                if tipo != "NEUTRO":
                    if solo_accion:
                        # FILTRO ACTIVADO: Solo mostramos si dice COMPRA, VENTA, ENTRADA o MOMENTUM
                        keywords_accion = ["COMPRA", "VENTA", "ENTRADA", "MOMENTUM"]
                        if any(k in tipo for k in keywords_accion):
                            agregar = True
                    else:
                        # FILTRO DESACTIVADO: Mostramos todo (incluido MANTENER)
                        agregar = True

                if agregar:
                    oportunidades.append({
                        "Ticker": ticker,
                        "Acción": tipo,
                        "Estrategia": strat_name,
                        "Detalle": detalle,
                        "Precio": f"${today['Close']:.2f}",
                        "Sharpe": f"{winner['Sharpe']:.2f}"
                    })
                    
                    # Feedback visual en tiempo real
                    icon = "🟢" if "COMPRA" in tipo or "ENTRADA" in tipo else "🔴" if "VENTA" in tipo else "🔵"
                    live_results.markdown(f"{icon} **{ticker}**: {tipo}")

        except Exception as e:
            # st.error(f"Error {ticker}: {e}") # Comentado para limpiar interfaz
            pass
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Auditoría completada.")
    progress_bar.empty()

    # --- TABLA DE RESULTADOS ---
    st.markdown("---")
    if oportunidades:
        st.subheader(f"🎯 Oportunidades Detectadas ({len(oportunidades)})")
        df_ops = pd.DataFrame(oportunidades)
        
        def color_highlight(val):
            if 'ENTRADA' in val or 'COMPRA' in val: return 'color: green; font-weight: bold'
            if 'VENTA' in val: return 'color: red; font-weight: bold'
            return 'color: blue' # Para Mantener
            
        st.dataframe(df_ops.style.applymap(color_highlight, subset=['Acción']), use_container_width=True)
    else:
        if solo_accion:
            st.success("✅ Todo tranquilo. No hay nuevas señales de Compra/Venta urgentes hoy.")
            st.info("Prueba desmarcar la casilla 'Mostrar SOLO Señales' para ver tus posiciones abiertas.")
        else:
            st.warning("Mercado Neutro (Sin señales activas).")