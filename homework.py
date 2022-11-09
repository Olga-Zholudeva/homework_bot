import logging
import os

import requests
import time

import telegram
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='main.log',
    filemode='w'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000, backupCount=5)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяем доступность переменных окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True


def get_api_answer(current_timestamp):
    """Делаем запрос к API домашки и получаем ответ."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise Exception('Статус ответа != 200')
    try:
        return response.json()
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')


def check_response(response):
    """Проверяем ответ API на корректность."""
    if len(response['homeworks']) == 0:
        raise Exception('Список работ пуст')
    if type(response.get('homeworks')) is not list:
        raise Exception('Тип данных отличен от спика')
    return response.get('homeworks')[0]


def parse_status(homework):
    """Готовим сообщение о статусе работы."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ "homework_name" отсутсвует в словаре homework')
    if 'status' not in homework:
        raise KeyError('Ключ "status" отсутсвует в словаре homework')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise Exception(f'Неизвестный статус {homework_status} работы {homework_name}')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}": {verdict}'


def send_message(bot, message):
    """Отправляем сообщение в ТГ."""
    try:
       bot.send_message(TELEGRAM_CHAT_ID, message)
       logger.info(f'Сообщение {message} отправлено в чат {TELEGRAM_CHAT_ID}')
    except Exception:
        logger.error('Сообщение не отправлено')


def main():
    """Основная логика работы бота."""
    status = ''
    error_message = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens():
        logger.error('Отсутствие обязательных переменных окружения')
        raise Exception('Отсутствие обязательных переменных окружения')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homework = check_response(response)
            message = parse_status(homework)
            if message != status:
                send_message(bot, message)
                status = message
            time.sleep(RETRY_TIME)
        except Exception as error:
            logger.error(error)
            message = f'Сбой в работе программы: {error}'
            if message != error_message:
                send_message(bot, message)
                error_message = message
            time.sleep(RETRY_TIME)

if __name__ == '__main__':
    main()
