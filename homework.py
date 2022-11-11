import logging
import os
import sys

import requests
import time
import telegram

from http import HTTPStatus
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'my_logger.log', maxBytes=50000000, backupCount=5
)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_RESULTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class MyCustomException(Exception):
    """Исключения для работы с HOMEWORK_BOT."""

    pass


def check_tokens():
    """Проверяем доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def get_api_answer(current_timestamp):
    """Делаем запрос к API домашки и получаем ответ."""
    timestamp = current_timestamp or int(time.time())
    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    try:
        response = requests.get(**request_params)
    except Exception:
        raise MyCustomException('Произошла ошибка сетовой связности')
    if response.status_code != HTTPStatus.OK:
        raise MyCustomException(
            f'Произошла ошибка: статус ответа {response.status_code}'
        )
    try:
        return response.json()
    except Exception as error:
        raise MyCustomException(f'Ошибка при запросе к основному API: {error}')


def check_response(response):
    """Проверяем ответ API на корректность."""
    logger.info('Начали приверку ответа')
    if not isinstance(response, dict):
        raise TypeError('Тип данных отличен от словаря')
    homeworks = response.get('homeworks')
    if 'homeworks' not in response or 'current_date' not in response:
        raise MyCustomException('В ответе нет нужного ключа')
    if not isinstance(homeworks, list):
        raise TypeError('Тип данных отличен от списка')
    return homeworks


def parse_status(homework):
    """Готовим сообщение о статусе работы."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ "homework_name" отсутсвует в словаре homework')
    if 'status' not in homework:
        raise KeyError('Ключ "status" отсутсвует в словаре homework')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_RESULTS:
        raise ValueError(
            f'Неизвестный статус {homework_status} работы {homework_name}'
        )
    verdict = HOMEWORK_RESULTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}": {verdict}'


def send_message(bot, message):
    """Отправляем сообщение в ТГ."""
    try:
        logger.info('Пробую отправить сообщение')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        raise telegram.TelegramError(
            f'Возникла ошибка при отправке сообщения: {error}'
        )
    except Exception as error:
        raise MyCustomException(
            f'Произошел сбой при отправке сообщения: {error}'
        )
    else:
        logger.info('Сообщение успешно отправлено')


def main():
    """Основная логика работы бота."""
    current_report = {
        'homework_name': '',
        'message': ''
    }
    prev_report = {
        'homework_name': '',
        'message': ''
    }
    current_timestamp = int(time.time())
    if not check_tokens():
        logger.critical('Отсутствие обязательных переменных окружения')
        sys.exit('Проблема с доступом')
    else:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if len(response['homeworks']) == 0:
                send_message(bot, 'От ревьюра нет новостей')
            else:
                current_timestamp = response.get('current_date')
                homework = check_response(response)
                message = parse_status(homework[0])
                homework_name = homework['homework_name']
                current_report['homework_name'] = homework_name
                current_report['message'] = message
            if current_report != prev_report:
                send_message(bot, message)
                prev_report = current_report.copy()
        except MyCustomException as error:
            logger.error(error)
            message = f'Сбой в работе программы: {error}'
            current_report['message'] = message
            if current_report != prev_report:
                send_message(bot, message)
                prev_report = current_report.copy()
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        filename='main.log',
        filemode='w'
    )
    main()
