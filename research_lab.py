# research_lab.py
import pandas as pd
import sys
# Truco para que encuentre las clases
sys.path.append('.') 
from classes.scout import AssetScout

# 1. DEFINIR EL UNIVERSO DE ACTIVOS
# Mezclamos Tech, Defensivas, Crypto y ETFs para ver diferencias
UNIVERSE = [
    "AMD", "TSLA", "NVDA",       # Volátiles / Tech
    "KO", "JNJ", "PG",           # Defensivas / Value
    "SPY", "QQQ",                # Índices
    "BTC-USD", "ETH-USD"         # Crypto
]

def run_lab():
    print("🧪 --- INICIANDO LABORATORIO QUANT --- 🧪")
    print("Objetivo: Clasificar activos por su mejor estrategia matemática.")
    print("-" * 60)
    
    results = []
    
    for ticker in UNIVERSE:
        # Instanciamos el Scout (Objeto)
        scout = AssetScout(ticker)
        
        # Ejecutamos la optimización
        winner = scout.optimize()
        
        if winner:
            results.append(winner)
            print(f"🏆 Ganador para {ticker}: {winner['Estrategia Ganadora']} ({winner['Retorno 5y']})")
            print(f"   ⚙️ Config: {winner['Mejores Parametros']}")
            print("-" * 30)

    # 2. GENERAR REPORTE FINAL
    df_results = pd.DataFrame(results)
    
    print("\n\n📑 --- REPORTE DE CLASIFICACIÓN FINAL ---")
    print(df_results.sort_values(by="Estrategia Ganadora"))
    
    # Guardar en CSV para que el bot lo use luego
    df_results.to_csv("data/optimized_portfolio.csv", index=False)
    print("\n✅ Configuración optimizada guardada en 'data/optimized_portfolio.csv'")

if __name__ == "__main__":
    run_lab()