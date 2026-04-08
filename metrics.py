import os
import requests
import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Конфигурация
MARZBAN_URL = os.getenv('MARZBAN_URL')
MARZBAN_USERNAME = os.getenv('MARZBAN_USERNAME')
MARZBAN_PASSWORD = os.getenv('MARZBAN_PASSWORD')
PUSHGATEWAY_URL1 = os.getenv('PUSHGATEWAY_URL1')
PUSHGATEWAY_URL2 = os.getenv('PUSHGATEWAY_URL2')
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
    
    return metrics, variables

def push_metrics():
    registry = CollectorRegistry()
    
    # Получение данных
    metrics, variables = get_marzban_metrics()
    print(variables)
    users = [None] * len(variables)
    for i, (key, value) in enumerate(variables.items()):
        users[i] = Gauge(f"marzban_user_{key}", f"Usage traffic of user {key}", registry=registry)
        users[i].set(metrics[f"marzban_user_{key}"])
    
    push_to_gateway(PUSHGATEWAY_URL2, job='users', registry=registry)

    # Определение метрик
    total_users = Gauge('marzban_users_total', 'Total number of users', registry=registry)
    active_users = Gauge('marzban_users_active', 'Active users count', registry=registry)
    disabled_users = Gauge('marzban_users_disabled', 'Disabled users count', registry=registry)
    upload_bytes = Gauge('marzban_traffic_upload_bytes', 'Total upload traffic', registry=registry)
    download_bytes = Gauge('marzban_traffic_download_bytes', 'Total download traffic', registry=registry)
    total_nodes = Gauge('marzban_nodes_total', 'Total number of nodes', registry=registry)
    # Установка значений
    total_users.set(metrics["marzban_total_users"])
    active_users.set(metrics["marzban_active_users"])
    disabled_users.set(metrics["marzban_disabled_users"])
    upload_bytes.set(metrics["marzban_total_upload_bytes"])
    download_bytes.set(metrics["marzban_total_download_bytes"])
    total_nodes.set(metrics["marzban_total_nodes"])
    
    # Отправка в Pushgateway
    push_to_gateway(PUSHGATEWAY_URL1, job='pushgateway', registry=registry)

if __name__ == "__main__":
    push_metrics()