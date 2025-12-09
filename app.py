# app.py - DASHBOARD PRINCIPAL OPTIMIZADO COMPLETO
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from datetime import datetime
from typing import Dict, Optional

sys.path.append('.') 

from classes.scout import AssetScout
from classes.strategies import (
    GoldenCrossStrategy, MeanReversionStrategy, BollingerBreakoutStrategy, 
    MACDStrategy, EMAStrategy, StochRSIStrategy, AwesomeOscillatorStrategy,
    SuperTrendStrategy, SqueezeMomentumStrategy, ADXStrategy
)
from classes.risk_manager import RiskManager
import config as cfg

# ============================================
# CONFIGURACIÓN GLOBAL
# ============================================

st.set_page_config(
    page_title=cfg.APP.app_name,
    layout=cfg.APP.layout,
    page_icon=cfg.APP.page_icon,
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    
    .signal-bullish {
        background-color: #10b981;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .signal-bearish {
        background-color: #ef4444;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .signal-neutral {
        background-color: #6b7280;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNCIONES HELPER
# ============================================

def instanciar_estrategia(strat_name: str):
    """Factory pattern para instanciar estrategias"""
    estrategias_map = {
        "Golden Cross": GoldenCrossStrategy,
        "Mean Reversion": MeanReversionStrategy,
        "Bollinger": BollingerBreakoutStrategy,
        "MACD": MACDStrategy,
        "EMA": EMAStrategy,
        "Stochastic": StochRSIStrategy,
        "Awesome": AwesomeOscillatorStrategy,
        "SuperTrend": SuperTrendStrategy,
        "Squeeze": SqueezeMomentumStrategy,
        "ADX": ADXStrategy
    }
    
    for keyword, strategy_class in estrategias_map.items():
        if keyword in strat_name:
            return strategy_class()
    
    return None


@st.cache_data(ttl=cfg.APP.cache_ttl_seconds)
def get_best_strategy(symbol: str) -> tuple:
    """Obtiene la mejor estrategia para un activo con cache"""
    try:
        scout = AssetScout(symbol)
        winner = scout.optimize()
        return winner, scout.data
    except Exception as e:
        st.error(f"❌ Error obteniendo estrategia para {symbol}: {e}")
        return None, None


def crear_grafico_avanzado(df: pd.DataFrame, strat_name: str, params: Dict) -> go.Figure:
    """Crea gráfico Plotly avanzado con subplots e indicadores"""
    
    # Crear subplots (precio + volumen + indicador)
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=('Precio y Señales', 'Volumen', 'Indicador Técnico')
    )
    
    # 1. CANDLESTICK
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Precio',
            increasing_line_color='#10b981',
            decreasing_line_color='#ef4444'
        ),
        row=1, col=1
    )
    
    # 2. SEÑALES DE COMPRA/VENTA
    buy_signals = df[df['Signal'].diff() == 1]
    sell_signals = df[df['Signal'].diff() == -1]
    
    if not buy_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=buy_signals.index,
                y=buy_signals['Low'] * 0.98,
                mode='markers',
                name='Señal Compra',
                marker=dict(symbol='triangle-up', size=15, color='#10b981', 
                           line=dict(width=2, color='white'))
            ),
            row=1, col=1
        )
    
    if not sell_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=sell_signals.index,
                y=sell_signals['High'] * 1.02,
                mode='markers',
                name='Señal Venta',
                marker=dict(symbol='triangle-down', size=15, color='#ef4444',
                           line=dict(width=2, color='white'))
            ),
            row=1, col=1
        )
    
    # 3. INDICADORES ESPECÍFICOS
    if "SuperTrend" in strat_name and 'SuperTrend' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SuperTrend'], 
                      line=dict(color='#8b5cf6', width=2), name='SuperTrend'),
            row=1, col=1
        )
    
    elif "EMA" in strat_name:
        ema_fast = df['Close'].ewm(span=params['fast'], adjust=False).mean()
        ema_slow = df['Close'].ewm(span=params['slow'], adjust=False).mean()
        fig.add_trace(
            go.Scatter(x=df.index, y=ema_fast, line=dict(color='#06b6d4', width=2), 
                      name=f"EMA {params['fast']}"),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=ema_slow, line=dict(color='#8b5cf6', width=2),
                      name=f"EMA {params['slow']}"),
            row=1, col=1
        )
    
    elif "Golden" in strat_name and 'SMA_Fast' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA_Fast'], line=dict(color='#06b6d4', width=2),
                      name=f"SMA {params['fast']}"),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA_Slow'], line=dict(color='#8b5cf6', width=2),
                      name=f"SMA {params['slow']}"),
            row=1, col=1
        )
    
    elif "Bollinger" in strat_name and 'BB_Upper' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['BB_Upper'], 
                      line=dict(color='#ef4444', width=1, dash='dash'), name='BB Superior'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['BB_Mid'], 
                      line=dict(color='#6b7280', width=1), name='BB Media'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['BB_Lower'],
                      line=dict(color='#10b981', width=1, dash='dash'), name='BB Inferior'),
            row=1, col=1
        )
    
    # 4. VOLUMEN
    colors = ['#10b981' if close > open_ else '#ef4444' 
              for close, open_ in zip(df['Close'], df['Open'])]
    
    fig.add_trace(
        go.Bar(x=df.index, y=df['Volume'], name='Volumen', 
               marker_color=colors, opacity=0.5),
        row=2, col=1
    )
    
    # 5. INDICADOR TÉCNICO
    if "Mean Reversion" in strat_name and 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#8b5cf6', width=2), 
                      name='RSI'),
            row=3, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    
    elif "MACD" in strat_name and 'MACD' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#06b6d4', width=2),
                      name='MACD'),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['Signal_Line'], 
                      line=dict(color='#ef4444', width=2), name='Signal'),
            row=3, col=1
        )
        fig.update_yaxes(title_text="MACD", row=3, col=1)
    
    elif "Squeeze" in strat_name and 'Momentum' in df.columns:
        colors_momentum = ['#10b981' if val > 0 else '#ef4444' for val in df['Momentum']]
        fig.add_trace(
            go.Bar(x=df.index, y=df['Momentum'], marker_color=colors_momentum, 
                  name='Momentum'),
            row=3, col=1
        )
        fig.update_yaxes(title_text="Momentum", row=3, col=1)
    
    elif "ADX" in strat_name and 'ADX' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['ADX'], line=dict(color='#8b5cf6', width=2),
                      name='ADX'),
            row=3, col=1
        )
        fig.add_hline(y=25, line_dash="dash", line_color="orange", row=3, col=1)
        fig.update_yaxes(title_text="ADX", row=3, col=1, range=[0, 100])
    
    # Layout
    fig.update_layout(
        title="Análisis Técnico Completo",
        xaxis_rangeslider_visible=False,
        height=900,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white'
    )
    
    fig.update_xaxes(title_text="Fecha", row=3, col=1)
    fig.update_yaxes(title_text="Precio ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volumen", row=2, col=1)
    
    return fig


def analizar_senal_actual(df: pd.DataFrame, strat_name: str, params: Dict) -> tuple:
    """Analiza la señal actual y retorna (texto, clase_css)"""
    today = df.iloc[-1]
    signal_val = today.get('Signal', 0)
    
    if "SuperTrend" in strat_name and 'Trend_Dir' in df.columns:
        if df['Trend_Dir'].iloc[-1] == 1:
            return "🟢 TENDENCIA ALCISTA (SUPERTREND)", "signal-bullish"
        else:
            return "🔻 TENDENCIA BAJISTA", "signal-bearish"
    
    elif "Squeeze" in strat_name and 'Momentum' in df.columns:
        mom = df['Momentum'].iloc[-1]
        if mom > 0:
            return f"🚀 MOMENTUM POSITIVO (+{mom:.2f})", "signal-bullish"
        else:
            return f"⬇️ MOMENTUM NEGATIVO ({mom:.2f})", "signal-bearish"
    
    elif "ADX" in strat_name and 'ADX' in df.columns:
        adx = df['ADX'].iloc[-1]
        if signal_val == 1:
            return f"💪 TENDENCIA FUERTE ALCISTA (ADX: {adx:.1f})", "signal-bullish"
        else:
            return f"😴 RANGO / NEUTRO (ADX: {adx:.1f})", "signal-neutral"
    
    elif "EMA" in strat_name:
        ema_fast = df['Close'].ewm(span=params['fast'], adjust=False).mean().iloc[-1]
        ema_slow = df['Close'].ewm(span=params['slow'], adjust=False).mean().iloc[-1]
        if ema_fast > ema_slow:
            return "📈 TENDENCIA ALCISTA (EMA)", "signal-bullish"
        else:
            return "📉 TENDENCIA BAJISTA (EMA)", "signal-bearish"
    
    elif "Golden" in strat_name:
        if signal_val == 1:
            return "🌟 GOLDEN CROSS - ALCISTA", "signal-bullish"
        else:
            return "💀 DEATH CROSS - BAJISTA", "signal-bearish"
    
    elif "Mean Reversion" in strat_name and 'RSI' in df.columns:
        rsi = today['RSI']
        if rsi < params.get('rsi_low', 30):
            return f"🎯 SOBREVENTA - COMPRA (RSI: {rsi:.1f})", "signal-bullish"
        elif rsi > params.get('rsi_high', 70):
            return f"⚠️ SOBRECOMPRA - VENTA (RSI: {rsi:.1f})", "signal-bearish"
        else:
            return f"➖ NEUTRAL (RSI: {rsi:.1f})", "signal-neutral"
    
    elif "MACD" in strat_name:
        return ("🔵 MACD ALCISTA", "signal-bullish") if signal_val == 1 else ("🔴 MACD BAJISTA", "signal-bearish")
    
    elif "Stochastic" in strat_name:
        return ("⚡ STOCH RSI - MOMENTUM ALCISTA", "signal-bullish") if signal_val == 1 else ("⚡ STOCH RSI - MOMENTUM BAJISTA", "signal-bearish")
    
    elif "Bollinger" in strat_name:
        return ("💥 RUPTURA ALCISTA (BOLLINGER)", "signal-bullish") if signal_val == 1 else ("➖ SIN RUPTURA", "signal-neutral")
    
    elif "Awesome" in strat_name:
        return ("🎸 AWESOME OSCILLATOR - ALCISTA", "signal-bullish") if signal_val == 1 else ("🎸 AWESOME OSCILLATOR - BAJISTA", "signal-bearish")
    
    return ("🟢 SEÑAL ALCISTA", "signal-bullish") if signal_val == 1 else ("🔴 SEÑAL BAJISTA", "signal-bearish")


# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("# 🎛️ Panel de Control")
    st.markdown("### 📊 Selección de Activo")
    
    sector_seleccionado = st.selectbox(
        "Sector",
        ["Todos", "INDICES", "CRYPTO", "TECH", "COMMUNICATIONS", 
         "CYCLICAL", "FINANCIALS", "HEALTHCARE", 
         "DEFENSIVE", "ENERGY", "INDUSTRIAL", "MATERIALS"]
    )
    
    tickers_disponibles = cfg.TICKERS if sector_seleccionado == "Todos" else cfg.ASSETS.get_by_sector(sector_seleccionado)
    ticker = st.selectbox("Ticker:", tickers_disponibles)
    
    st.markdown("---")
    st.markdown("### 📍 Información")
    sector = cfg.ASSETS.get_sector_for_ticker(ticker)
    st.info(f"**Sector:** {sector}")
    
    strategy_config = cfg.STRATEGY_MAP_OBJ.get_strategy(ticker)
    if strategy_config:
        st.success(f"**Estrategia:** {strategy_config['strategy']}")
    
    st.markdown("---")
    st.markdown("### 💰 Gestión de Riesgo")
    capital = st.number_input("Capital ($)", min_value=100.0, value=float(cfg.RISK.capital_total), step=500.0)
    riesgo_pct = st.slider("Riesgo por Trade (%)", min_value=0.5, max_value=10.0, value=float(cfg.RISK.riesgo_por_operacion * 100), step=0.5)
    
    st.markdown("---")
    st.markdown("### 🔗 Enlaces Rápidos")
    st.page_link("pages/radar.py", label="🎯 Radar de Oportunidades", icon="🎯")
    
    st.markdown("---")
    st.caption(f"v{cfg.APP.app_version} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# ============================================
# CONTENIDO PRINCIPAL
# ============================================

st.markdown('<h1 class="main-header">⚡ TradeXpert: Piloto Automático</h1>', unsafe_allow_html=True)

with st.spinner(f"🤖 Analizando {ticker} con IA..."):
    winner, df = get_best_strategy(ticker)

if winner and df is not None and not df.empty:
    today = df.iloc[-1]
    strat_name = winner['Estrategia']
    params = winner['Params']
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análisis Técnico", "📈 Performance", "🎯 Trading Setup", "ℹ️ Información"])
    
    # TAB 1: ANÁLISIS TÉCNICO
    with tab1:
        st.success(f"✅ **Estrategia Óptima Detectada:** {strat_name}")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("💵 Precio Actual", f"${today['Close']:.2f}")
        with col2:
            cambio_diario = ((today['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100
            st.metric("📊 Cambio 24h", f"{cambio_diario:+.2f}%")
        with col3:
            st.metric("📈 Retorno 2Y", f"{winner['Retorno']*100:+.0f}%")
        with col4:
            st.metric("⚡ Sharpe Ratio", f"{winner['Sharpe']:.2f}")
        with col5:
            st.metric("📉 Max Drawdown", f"{winner['Drawdown']*100:.1f}%")
        
        st.markdown("---")
        texto_senal, color_clase = analizar_senal_actual(df, strat_name, params)
        st.markdown(f'<div class="{color_clase}">{texto_senal}</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        strat_obj = instanciar_estrategia(strat_name)
        if strat_obj:
            df = strat_obj.generate_signals(df, params)
            fig = crear_grafico_avanzado(df, strat_name, params)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"⚠️ No se pudo instanciar la estrategia: {strat_name}")
    
    # TAB 2: PERFORMANCE
    with tab2:
        st.subheader("📈 Métricas de Performance Detalladas")
        returns = df['Close'].pct_change() * df.get('Signal', 0).shift(1)
        equity = (1 + returns).cumprod()
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("### 📊 Métricas Clave")
            metrics_data = {
                "Métrica": ["Retorno Total", "Sharpe Ratio", "Max Drawdown", "Retorno Anualizado"],
                "Valor": [f"{winner['Retorno']*100:.2f}%", f"{winner['Sharpe']:.2f}", 
                         f"{winner['Drawdown']*100:.2f}%", f"{(winner['Retorno']/2)*100:.2f}%"]
            }
            st.dataframe(pd.DataFrame(metrics_data), use_container_width=True, hide_index=True)
        
        with col_p2:
            st.markdown("### 💰 Simulación de Capital")
            capital_inicial = 10000
            capital_final = capital_inicial * (1 + winner['Retorno'])
            ganancia = capital_final - capital_inicial
            st.metric("Capital Inicial", f"${capital_inicial:,.2f}")
            st.metric("Capital Final", f"${capital_final:,.2f}", f"+${ganancia:,.2f}")
            st.metric("Ganancia %", f"{winner['Retorno']*100:.2f}%")
        
        st.markdown("### 📈 Curva de Equity")
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(x=equity.index, y=equity.values, fill='tozeroy', 
                                        name='Equity', line=dict(color='#667eea', width=2)))
        fig_equity.update_layout(title="Evolución del Capital", xaxis_title="Fecha", 
                                yaxis_title="Equity (múltiplo)", template='plotly_white', height=400)
        st.plotly_chart(fig_equity, use_container_width=True)
    
    # TAB 3: TRADING SETUP
    with tab3:
        st.subheader("🎯 Setup de Trading Recomendado")
        risk_mgr = RiskManager(df)
        signal_actual = df.iloc[-1].get('Signal', 0)
        direction = "LONG" if signal_actual == 1 else "SHORT"
        setup = risk_mgr.get_trade_setup(entry_price=today['Close'], direction=direction, 
                                         atr_multiplier=cfg.RISK.atr_multiplier, 
                                         risk_reward_ratio=cfg.RISK.rr_ratio)
        
        if setup:
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.markdown("### 📍 Niveles de Precio")
                st.metric("🎯 Entrada", f"${setup['entry']:.2f}")
                st.metric("🛡️ Stop Loss", f"${setup['stop_loss']:.2f}", 
                         f"{((setup['stop_loss']/setup['entry']-1)*100):.2f}%")
                st.metric("💰 Take Profit", f"${setup['take_profit']:.2f}",
                         f"+{((setup['take_profit']/setup['entry']-1)*100):.2f}%")
            
            with col_s2:
                st.markdown("### 💵 Gestión de Capital")
                riesgo_decimal = riesgo_pct / 100
                units = risk_mgr.calculate_position_size(capital, riesgo_decimal, setup)
                inversion = units * setup['entry']
                st.metric("📦 Unidades", f"{units:.4f}")
                st.metric("💰 Inversión Total", f"${inversion:,.2f}")
                st.metric("🎲 Riesgo ($)", f"${capital * riesgo_decimal:,.2f}")
            
            with col_s3:
                st.markdown("### 📊 Ratios")
                riesgo_trade = abs(setup['stop_loss'] - setup['entry']) * units
                ganancia_potencial = abs(setup['take_profit'] - setup['entry']) * units
                st.metric("📉 Riesgo/Trade", f"${riesgo_trade:.2f}")
                st.metric("📈 Ganancia Potencial", f"${ganancia_potencial:.2f}")
                st.metric("⚖️ R:R Ratio", f"1:{setup['rr_ratio']}")
            
            st.markdown("---")
            st.markdown("### 📊 Visualización del Setup")
            df_reciente = df.tail(50)
            fig_setup = go.Figure()
            fig_setup.add_trace(go.Candlestick(x=df_reciente.index, open=df_reciente['Open'], 
                                               high=df_reciente['High'], low=df_reciente['Low'], 
                                               close=df_reciente['Close'], name='Precio'))
            fig_setup.add_hline(y=setup['entry'], line_dash="solid", line_color="blue", 
                               annotation_text="ENTRADA", annotation_position="right")
            fig_setup.add_hline(y=setup['stop_loss'], line_dash="dash", line_color="red",
                               annotation_text="STOP LOSS", annotation_position="right")
            fig_setup.add_hline(y=setup['take_profit'], line_dash="dash", line_color="green",
                               annotation_text="TAKE PROFIT", annotation_position="right")
            fig_setup.update_layout(title=f"Setup de Trading - {ticker} ({direction})", 
                                   xaxis_title="Fecha", yaxis_title="Precio ($)", 
                                   template='plotly_white', height=500, showlegend=True)
            st.plotly_chart(fig_setup, use_container_width=True)
        else:
            st.warning("⚠️ No se pudo calcular el setup (ATR insuficiente)")
    
    # TAB 4: INFORMACIÓN
    with tab4:
        st.subheader("ℹ️ Información Detallada del Activo")
        col_i1, col_i2 = st.columns(2)
        
        with col_i1:
            st.markdown("### 📊 Datos del Activo")
            st.info(f"""
            **Ticker:** {ticker}
            **Sector:** {sector}
            **Estrategia Óptima:** {strat_name}
            **Período:** {df.index[0].strftime('%Y-%m-%d')} a {df.index[-1].strftime('%Y-%m-%d')}
            **Días de Datos:** {len(df)}
            """)
        
        with col_i2:
            st.markdown("### ⚙️ Parámetros de la Estrategia")
            st.code(str(params), language="python")
        
        st.markdown("---")
        st.markdown("### 📈 Estadísticas del Precio")
        price_stats = {
            "Métrica": ["Precio Actual", "Máximo 52 Semanas", "Mínimo 52 Semanas", 
                       "Promedio Móvil 50d", "Promedio Móvil 200d", "Volatilidad (30d)"],
            "Valor": [
                f"${today['Close']:.2f}",
                f"${df['High'].tail(252).max():.2f}",
                f"${df['Low'].tail(252).min():.2f}",
                f"${df['Close'].rolling(50).mean().iloc[-1]:.2f}",
                f"${df['Close'].rolling(200).mean().iloc[-1]:.2f}",
                f"{df['Close'].pct_change().tail(30).std() * 100:.2f}%"
            ]
        }
        st.dataframe(pd.DataFrame(price_stats), use_container_width=True, hide_index=True)

else:
    st.error("❌ Error cargando datos del activo. Intenta con otro ticker.")
    if winner is None:
        st.info("💡 Posibles causas: ticker inválido, sin datos suficientes, o error de conexión.")

# FOOTER
st.markdown("---")
st.caption(f"""
    {cfg.APP.app_name} v{cfg.APP.app_version} | 
    Desarrollado con ❤️ y ☕ | 
    © 2024 | 
    📧 Soporte: support@tradexpert.com
""")
