# utils/news_sentiment.py
import requests
import xml.etree.ElementTree as ET
from textblob import TextBlob

def get_market_sentiment(symbol):
    """
    Motor V2: Descarga noticias desde Google News RSS (Más estable que Yahoo).
    Retorna: Score (-1 a 1) y lista de titulares.
    """
    try:
        # 1. Conectamos con Google News RSS
        # Buscamos "{SYMBOL} stock" para filtrar noticias financieras
        url = f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en"
        
        # Usamos un timeout para que no se cuelgue si Google tarda
        response = requests.get(url, timeout=5)
        
        # 2. Parseamos (leemos) el XML recibido
        root = ET.fromstring(response.content)
        
        # Buscamos los items (noticias)
        news_items = root.findall('.//item')
        
        if not news_items:
            return {"score": 0, "status": "NEUTRO 😐", "headlines": []}
        
        total_polarity = 0
        count = 0
        headlines = []
        
        # Analizamos las 5 primeras noticias
        for item in news_items[:5]:
            title_raw = item.find('title').text
            link = item.find('link').text
            
            # Limpieza: Google suele poner el nombre del diario al final (ej: "Tesla sube - CNN")
            # Lo quitamos para analizar solo la frase
            title_clean = title_raw.split(' - ')[0]
            
            # Análisis de Sentimiento
            analysis = TextBlob(title_clean)
            polarity = analysis.sentiment.polarity
            
            # Filtro: Ignoramos noticias con sentimiento 0.0 (títulos muy neutros) para no diluir
            if polarity != 0:
                total_polarity += polarity
                count += 1
            
            headlines.append({"title": title_clean, "url": link, "score": polarity})
            
        # Promedio del sentimiento
        if count > 0:
            avg_score = total_polarity / count
        else:
            avg_score = 0 # Si todo fue neutro
            
        # Interpretación Humana
        if avg_score > 0.05:
            status = "POSITIVO 😀"
            color = "green"
        elif avg_score < -0.05:
            status = "NEGATIVO 😡"
            color = "red"
        else:
            status = "NEUTRO 😐"
            color = "gray"
            
        return {
            "score": avg_score,
            "status": status,
            "color": color,
            "headlines": headlines # Devolvemos las noticias para la lista
        }

    except Exception as e:
        print(f"Error en sentimiento: {e}")
        return {"score": 0, "status": "ERROR", "headlines": []}