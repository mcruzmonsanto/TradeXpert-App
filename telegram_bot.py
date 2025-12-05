# telegram_bot.py
import requests
import config as cfg

def send_msg(message):
    """Envía un mensaje a tu Telegram personal"""
    try:
        url = f"https://api.telegram.org/bot{cfg.TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": cfg.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown" # Permite usar negritas
        }
        requests.post(url, data=payload)
        print("📨 Notificación enviada a Telegram.")
    except Exception as e:
        print(f"❌ Error enviando Telegram: {e}")

# Prueba unitaria (Solo si ejecutas este archivo directamente)
if __name__ == "__main__":
    send_msg("👋 Hola Jefe, soy TradeXpert. Tu sistema de alertas está activo.")