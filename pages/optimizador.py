# pages/optimizador.py
import streamlit as st
import pandas as pd
import time
import sys

# Importamos el motor OOP
sys.path.append('.') 
from classes.scout import AssetScout
import config as cfg

st.set_page_config(page_title="IA Scout Optimizer", layout="wide", page_icon="🤖")

st.title("🤖 IA Scout: Optimizador de Estrategias")
st.markdown("""
Este módulo utiliza **Programación Orientada a Objetos (OOP)** para auditar cada activo.
El algoritmo prueba cientos de combinaciones matemáticas y determina la "Personalidad" del activo.
""")

# --- CONFIGURACIÓN ---
st.sidebar.header("Configuración del Escáner")
# Permitimos elegir del universo en config o añadir manuales
selected_tickers = st.sidebar.multiselect("Selecciona Activos a Auditar:", cfg.TICKERS, default=cfg.TICKERS[:3])

start_btn = st.sidebar.button("🚀 INICIAR ESCANEO DE IA")

# --- LÓGICA DE OPTIMIZACIÓN ---
if start_btn:
    if not selected_tickers:
        st.error("Por favor selecciona al menos un activo.")
    else:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        st.markdown("### 📡 Resultados del Escaneo en Tiempo Real")
        result_container = st.container()

        # Bucle de Optimización
        for i, ticker in enumerate(selected_tickers):
            status_text.text(f"Analizando {ticker}... (Esto puede tardar unos segundos)")
            
            # 1. Instanciamos el Objeto Scout (OOP)
            scout = AssetScout(ticker)
            
            # 2. Ejecutamos el método optimize()
            winner = scout.optimize()
            
            if winner:
                results.append(winner)
                
                # Visualización instantánea tipo tarjeta
                with result_container:
                    if "Mean Reversion" in winner['Estrategia Ganadora']:
                        color = "green" # Rebote
                        icon = "💎"
                    else:
                        color = "blue"  # Tendencia
                        icon = "📈"
                        
                    st.success(f"""
                    **{icon} {winner['Ticker']}** -> Mejor Estrategia: **{winner['Estrategia Ganadora']}**
                    \nRetorno 5 años: **{winner['Retorno 5y']}** | Config: `{winner['Mejores Parametros']}`
                    """)
            
            # Actualizar barra
            progress_bar.progress((i + 1) / len(selected_tickers))
            time.sleep(0.1)

        status_text.text("✅ ¡Escaneo Completo!")
        progress_bar.empty()

        # --- TABLA RESUMEN ---
        st.markdown("---")
        st.subheader("📑 Reporte Ejecutivo de Asignación")
        
        if results:
            df_res = pd.DataFrame(results)
            
            # Formato bonito
            st.dataframe(df_res.style.applymap(
                lambda x: 'color: green; font-weight: bold' if 'Mean' in str(x) else 'color: blue; font-weight: bold', 
                subset=['Estrategia Ganadora']
            ))
            
            # Botón de Descarga
            csv = df_res.to_csv(index=False).encode('utf-8')
            st.download_button(
                "💾 Descargar Configuración Óptima (CSV)",
                csv,
                "portfolio_optimizado.csv",
                "text/csv",
                key='download-csv'
            )
            
            st.info("💡 **Tip del Mentor:** Descarga este CSV. Próximamente usaremos este archivo para que el bot configure automáticamente cada acción con su estrategia ideal.")
        else:
            st.warning("No se obtuvieron resultados. Revisa la conexión a datos.")