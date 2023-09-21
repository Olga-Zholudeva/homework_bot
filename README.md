# Бот для проверки статуса домашней работы на код ревью в Яндекс.Практикум

## Что умеет бот:

- раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса отправляет соответствующее уведомление в Telegram;
- логгирует свою работу и сообщает  о важных проблемах сообщением в Telegram

Эндпоинт API Практикум.Домашка: **https://practicum.yandex.ru/api/user_api/homework_statuses/**

## Запуск проекта:

- Клонируем репозиторий: **git clone [homework_bot](https://github.com/Olga-Zholudeva/homework_bot)**
- Cоздаем и активировируем виртуальное окружение: **python3 -m venv env source env/bin/activate**
- Устанавливаем зависимости из файла requirements.txt: **pip install -r requirements.txt**
- Импортируем токены для ЯндексюПрактикум и для Телеграмм:  
      **export PRACTICUM_TOKEN=<PRACTICUM_TOKEN>**  
      **export TELEGRAM_TOKEN=<TELEGRAM_TOKEN>**  
      **export CHAT_ID=<CHAT_ID>**  
- Запускаем бота: **python homework.py**  


## Проект выполнен:

**Ольга Жолудева**
