# pages/radar.py
import streamlit as st
import pandas as pd
import sys

# Importamos el cerebro
sys.path.append('.') 
from classes.scout import AssetScout
from classes.strategies import GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, MACDStrategy
import config as cfg

st.set_page_config(page_title="Radar de Oportunidades", layout="wide", page_icon="📡")

st.title("📡 Radar de Oportunidades: Escaneo Masivo V2")
st.markdown("Auditoría en tiempo real de todo tu universo de activos.")

if st.button("🚀 INICIAR ESCANEO GLOBAL"):
    
    oportunidades = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    live_results = st.container()

    total_assets = len(cfg.TICKERS)
    
    for i, ticker in enumerate(cfg.TICKERS):
        status_text.text(f"Auditando {ticker} ({i+1}/{total_assets})...")
        
        try:
            # 1. Optimización Rápida
            scout = AssetScout(ticker)
            winner = scout.optimize()
            
            if winner and scout.data is not None and not scout.data.empty:
                df = scout.data
                strat_name = winner['Estrategia']
                params = winner['Params']
                
                # 2. Instanciar estrategia ganadora
                strat_obj = None
                if "Golden Cross" in strat_name: strat_obj = GoldenCrossStrategy()
                elif "Mean Reversion" in strat_name: strat_obj = MeanReversionStrategy()
                elif "Bollinger" in strat_name: strat_obj = BollingerBreakoutStrategy()
                elif "MACD" in strat_name: strat_obj = MACDStrategy()
                
                # 3. Backtest para obtener señales
                _ = strat_obj.backtest(df, params)
                
                # --- LÓGICA DE DETECCIÓN MEJORADA (V2) ---
                # Ya no buscamos solo el cruce exacto de ayer, sino el ESTADO actual.
                
                # Último dato
                today = df.iloc[-1]
                signal_val = today['Signal'] # 1 (Comprado) o 0 (Vendido)
                
                tipo = "NEUTRO"
                detalle = ""
                
                # A) Si el sistema dice que debemos estar COMPRADOS (Signal=1)
                if signal_val == 1:
                    tipo = "COMPRA / MANTENER"
                    
                    # Refinamos el mensaje
                    if "Mean Reversion" in strat_name:
                        detalle = f"Rebote Activo (RSI {today['RSI']:.1f})"
                    elif "Golden Cross" in strat_name:
                        detalle = f"Tendencia Alcista (SMA {params['fast']} > {params['slow']})"
                    elif "Bollinger" in strat_name:
                        detalle = f"Ruptura de Volatilidad ({today['Close']:.2f})"
                    elif "MACD" in strat_name:
                        detalle = "Momentum Positivo (MACD > Signal)"

                # B) Caso Especial: Mean Reversion VENTA
                # En Mean Reversion, a veces queremos saber si hay que VENDER ya
                elif "Mean Reversion" in strat_name:
                    if today['RSI'] > params['rsi_high']:
                        tipo = "VENTA"
                        detalle = f"Sobrecompra Extrema (RSI {today['RSI']:.1f})"

                # 4. FILTRO FINAL: ¿Lo mostramos?
                # Mostramos si es VENTA o si es COMPRA
                if tipo != "NEUTRO":
                    oportunidades.append({
                        "Ticker": ticker,
                        "Estrategia": strat_name,
                        "Acción": tipo,
                        "Detalle": detalle,
                        "Precio": f"${today['Close']:.2f}",
                        "Sharpe": f"{winner['Sharpe']:.2f}"
                    })
                    
                    # Feedback visual inmediato
                    icon = "🟢" if "COMPRA" in tipo else "🔴"
                    live_results.markdown(f"{icon} **{ticker}**: {tipo} ({strat_name})")

        except Exception as e:
            print(f"Error en {ticker}: {e}")
            
        progress_bar.progress((i + 1) / total_assets)
    
    status_text.text("✅ Escaneo Finalizado.")
    progress_bar.empty()

    # --- TABLA DE RESULTADOS ---
    st.markdown("---")
    if oportunidades:
        st.subheader(f"📋 Se encontraron {len(oportunidades)} Activos Activos")
        df_ops = pd.DataFrame(oportunidades)
        
        def color_highlight(val):
            color = 'green' if 'COMPRA' in val else 'red' if 'VENTA' in val else 'black'
            return f'color: {color}; font-weight: bold'
            
        st.dataframe(df_ops.style.applymap(color_highlight, subset=['Acción']), use_container_width=True)
    else:
        st.warning("No hay señales activas. Mercado 100% Neutro (Poco probable).")