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

def get_marzban_metrics():
    # Аутентификация
    session = requests.Session()
    session.cert = (CLIENT_CERT_PATH, CLIENT_KEY_PATH)
    login_data = {
        "username": MARZBAN_USERNAME,
        "password": MARZBAN_PASSWORD
    }
    
    # Получение токена
    response = session.post(f"{MARZBAN_URL}/api/admin/token", data=login_data)
    token = response.json()["access_token"]
    
    # Заголовки с токеном
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Сбор метрик
    metrics = {}
    
    # 1. Статистика пользователей
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
        
    metrics["marzban_total_users"] = len(users)
    metrics["marzban_active_users"] = len([u for u in users if u.get("status") == "active"])
    metrics["marzban_disabled_users"] = len([u for u in users if u.get("status") == "disabled"])
    
    # 2. Использование трафика
    total_upload = 0
    total_download = 0
    
    for user in users:
        total_upload += user.get("used_traffic", 0)
        total_download += user.get("download", 0)
    
    metrics["marzban_total_upload_bytes"] = total_upload
    metrics["marzban_total_download_bytes"] = total_download
    
    # 3. Статистика по нодам (если есть)
    try:
        nodes_response = session.get(f"{MARZBAN_URL}/api/nodes", headers=headers)
        nodes = nodes_response.json()
        metrics["marzban_total_nodes"] = len(nodes)
    except:
        metrics["marzban_total_nodes"] = 0
    now = datetime.now()

    with open(f'log_{now.strftime("%Y_%m_%d_%H_%M_%S")}.txt', 'w') as file:
        file.write(str(metrics))
        file.write(str(variables))
    #return metrics, variables

def reset_traffic_metrics():
    session = requests.Session()
    session.cert = (CLIENT_CERT_PATH, CLIENT_KEY_PATH)
    login_data = {
        "username": MARZBAN_USERNAME,
        "password": MARZBAN_PASSWORD
    }
    
    # Получение токена
    response = session.post(f"{MARZBAN_URL}/api/admin/token", data=login_data)
    token = response.json()["access_token"]
    
    # Заголовки с токеном
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    reset_response = session.post(f"{MARZBAN_URL}/api/users/reset", headers=headers)
    reset = reset_response

if __name__ == "__main__":
    get_marzban_metrics()
    reset_traffic_metrics()