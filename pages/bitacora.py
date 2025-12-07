# pages/bitacora.py
import streamlit as st
import pandas as pd
import os
import yfinance as yf

st.set_page_config(page_title="Bitácora & Performance", layout="wide", page_icon="📔")

LOG_FILE = "data/bitacora_trades.csv"

st.title("📔 Bitácora de Trading")
st.markdown("Registro oficial de operaciones y métricas de rendimiento.")

# --- CARGAR DATOS ---
if not os.path.exists(LOG_FILE):
    st.info("Aún no has registrado ninguna operación desde el Radar.")
    st.stop()

df = pd.read_csv(LOG_FILE)

# --- MÉTRICAS GLOBALES ---
trades_cerrados = df[df['Status'] == 'CERRADA']
if not trades_cerrados.empty:
    total_pl = trades_cerrados['Resultado'].sum()
    win_rate = (len(trades_cerrados[trades_cerrados['Resultado'] > 0]) / len(trades_cerrados)) * 100
    best_trade = trades_cerrados['Resultado'].max()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("P&L Total Realizado", f"${total_pl:.2f}", delta_color="normal")
    c2.metric("Win Rate", f"{win_rate:.1f}%")
    c3.metric("Mejor Trade", f"${best_trade:.2f}")
    c4.metric("Operaciones Cerradas", len(trades_cerrados))
    st.markdown("---")

# --- GESTIÓN DE POSICIONES ABIERTAS ---
st.subheader("🟢 Posiciones Abiertas (Cartera Actual)")
abiertas = df[df['Status'] == 'ABIERTA']

if abiertas.empty:
    st.info("No tienes posiciones abiertas.")
else:
    # Mostramos una tarjeta por cada posición abierta para poder cerrarla
    for index, row in abiertas.iterrows():
        with st.container(border=True):
            cols = st.columns([2, 2, 2, 1])
            
            # Info Básica
            cols[0].markdown(f"**{row['Ticker']}** ({row['Accion']})")
            cols[0].caption(f"Fecha: {row['Fecha']}")
            
            # Info Precio
            cols[1].markdown(f"Entrada: **${row['Precio_Entrada']}**")
            cols[1].caption(f"Unidades: {row['Unidades']}")
            
            # Precio Actual (Live)
            try:
                current_price = yf.Ticker(row['Ticker']).fast_info['last_price']
                pnl_latente = (current_price - row['Precio_Entrada']) * row['Unidades']
                if row['Accion'] == 'SHORT': pnl_latente = -pnl_latente # Invertir si es short
                
                color = "green" if pnl_latente > 0 else "red"
                cols[2].metric("Precio Actual", f"${current_price:.2f}", f"${pnl_latente:.2f}")
            except:
                cols[2].warning("Sin datos live")
                current_price = row['Precio_Entrada']

            # ACCIÓN DE CIERRE
            with cols[3]:
                if st.button("Cerrar Posición", key=f"close_{index}"):
                    # Calcular P&L Final
                    pnl_final = (current_price - row['Precio_Entrada']) * row['Unidades']
                    if row['Accion'] == 'SHORT': pnl_final = -pnl_final
                    
                    # Actualizar DataFrame
                    df.at[index, 'Status'] = 'CERRADA'
                    df.at[index, 'Precio_Salida'] = round(current_price, 2)
                    df.at[index, 'Resultado'] = round(pnl_final, 2)
                    
                    # Guardar
                    df.to_csv(LOG_FILE, index=False)
                    st.success(f"Posición cerrada. P&L: ${pnl_final:.2f}")
                    st.rerun()

# --- HISTORIAL COMPLETO ---
st.subheader("📜 Historial de Operaciones Cerradas")
if not trades_cerrados.empty:
    # Estilizar la tabla
    def color_pnl(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        trades_cerrados[['Fecha', 'Ticker', 'Accion', 'Estrategia', 'Precio_Entrada', 'Precio_Salida', 'Resultado']]
        .style.applymap(color_pnl, subset=['Resultado']),
        use_container_width=True
    )
    
    # Descargar CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Descargar Historial Completo", csv, "mi_trading_journal.csv")
