# utils/news_sentiment.py
import yfinance as yf
from textblob import TextBlob
import pandas as pd

def get_market_sentiment(symbol):
    """
    Descarga noticias recientes de Yahoo Finance y calcula el sentimiento promedio.
    Retorna: Score (-1 a 1) y lista de titulares.
    """
    try:
        ticker = yf.Ticker(symbol)
        news_list = ticker.news
        
        if not news_list:
            return {"score": 0, "status": "NEUTRO 😐", "headlines": []}
        
        total_polarity = 0
        count = 0
        headlines = []
        
        for item in news_list:
            title = item.get('title', '')
            link = item.get('link', '')
            
            # Análisis de Sentimiento con TextBlob
            # Polarity va de -1 (Muy Negativo) a +1 (Muy Positivo)
            analysis = TextBlob(title)
            polarity = analysis.sentiment.polarity
            
            total_polarity += polarity
            count += 1
            headlines.append({"title": title, "url": link, "score": polarity})
            
        # Promedio del sentimiento
        if count > 0:
            avg_score = total_polarity / count
        else:
            avg_score = 0
            
        # Interpretación Humana
        if avg_score > 0.1:
            status = "POSITIVO 😀"
            color = "green"
        elif avg_score < -0.1:
            status = "NEGATIVO 😡"
            color = "red"
        else:
            status = "NEUTRO 😐"
            color = "gray"
            
        return {
            "score": avg_score,
            "status": status,
            "color": color,
            "headlines": headlines[:3] # Devolvemos solo las 3 últimas
        }

    except Exception as e:
        print(f"Error en sentimiento: {e}")
        return {"score": 0, "status": "ERROR", "headlines": []}