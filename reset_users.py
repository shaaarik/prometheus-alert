import os
import requests
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Конфигурация
MARZBAN_URL = os.getenv('MARZBAN_URL')
MARZBAN_USERNAME = os.getenv('MARZBAN_USERNAME')
MARZBAN_PASSWORD = os.getenv('MARZBAN_PASSWORD')
CLIENT_CERT_PATH = os.getenv('CLIENT_CERT_PATH')
CLIENT_KEY_PATH = os.getenv('CLIENT_KEY_PATH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_ID = os.getenv('TELEGRAM_BOT_ID')


def send_telegram_message(message, chat_id, token):
    """Отправка сообщения через Telegram Bot API"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Сообщение отправлено в Telegram")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        return False

def get_marzban_metrics():
    session = requests.Session()
    session.cert = (CLIENT_CERT_PATH, CLIENT_KEY_PATH)
    login_data = {
        "username": MARZBAN_USERNAME,
        "password": MARZBAN_PASSWORD
    }
    
    response = session.post(f"{MARZBAN_URL}/api/admin/token", data=login_data)
    token = response.json()["access_token"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    metrics = {}
    
    users_response = session.get(f"{MARZBAN_URL}/api/users", headers=headers)
    users = users_response.json()["users"]
    variables = {}
    usernames = []

    for user in users:
        username = user.get("username")
        variables[username] = None
        user_used_traffic = user.get("used_traffic")
        variables[username] = user_used_traffic

        metrics[f"marzban_user_{username}"] = user_used_traffic
        
    print(metrics)
    sorted_metrics = dict(sorted(metrics.items(), key=lambda item: item[1], reverse=True))
    
    summary = "📊 *Топ пользователей по трафику:*\n\n"
    
    for i, (username, traffic) in enumerate(sorted_metrics.items(), 1):
        if i > 15: 
            break
        
        traffic_gb = traffic / 1024 / 1024 / 1024
        
        medal = ""
        if i == 1:
            medal = "🥇 "
        elif i == 2:
            medal = "🥈 "
        elif i == 3:
            medal = "🥉 "
        
        clean_name = username.replace('marzban_user_', '')
        summary += f"{medal}*{clean_name}*: `{traffic_gb:.2f} GB` ({traffic:,} bytes)\n"
    
    total_users = len(metrics)
    total_traffic = sum(metrics.values())
    total_traffic_gb = total_traffic / 1024 / 1024 / 1024
    
    summary += f"\n📈 *Всего пользователей:* {total_users}\n"
    summary += f"💾 *Общий трафик:* {total_traffic_gb:.2f} GB\n"
    
    send_telegram_message(summary, BOT_ID, BOT_TOKEN)
    
    return metrics, variables

def reset_traffic_metrics():
    session = requests.Session()
    session.cert = (CLIENT_CERT_PATH, CLIENT_KEY_PATH)
    login_data = {
        "username": MARZBAN_USERNAME,
        "password": MARZBAN_PASSWORD
    }
    
    response = session.post(f"{MARZBAN_URL}/api/admin/token", data=login_data)
    token = response.json()["access_token"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    reset_response = session.post(f"{MARZBAN_URL}/api/users/reset", headers=headers)
    reset = reset_response

if __name__ == "__main__":
    get_marzban_metrics()
    reset_traffic_metrics()


 
