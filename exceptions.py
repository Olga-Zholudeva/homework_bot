class MyCustomExceptionSendMessage(Exception):
    """Ошибки работы модуля HOMEWORK_BOT, пересылаемые в ТГ."""
    pass

class MyCustomExceptionNotSendMessage(Exception):
    """Ошибки работы модуля HOMEWORK_BOT, НЕ пересылаемые в ТГ."""
    pass
