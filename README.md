# Установка Pushgateway
docker run -d \
  -p 9091:9091 \
  --name pushgateway \
  prom/pushgateway

  

  # Добавить в crontab
*/5 * * * * /usr/bin/python3 /home/john/prometheus_alert/metrics.py


# Если python  защищен от изменений в хост системе

создаем скрипт

#!/bin/bash
# Полный путь к вашему виртуальному окружению
source /home/john/prometheus_alert/venv/bin/activate
python /home/john/prometheus_alert/metrics.py
