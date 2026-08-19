import logging

# Предотвращает сообщения "No handler found", пока пользователь/тесты не настроят логгер
logging.getLogger("aiokaspi").addHandler(logging.NullHandler())
