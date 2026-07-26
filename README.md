# Kaspi Python SDK (Auth Client)

Библиотека для аутентификации в API Kaspi Pay с использованием мобильного протокола (iOS/Android).

> [!WARNING]
> **Проект находится в стадии активной разработки.**  
> Вся основная разработка ведется в ветке `dev`.Архитектура библиотеки будет меняться, многие планируемые модули еще не реализованы. Однако базовый и самый сложный модуль — **авторизация** — полностью готов, протестирован и стабильно работает.

Это не просто легкая HTTP-обертка: библиотека проектируется как надежный **мини-фреймворк** для работы с Kaspi Pay. В коде учтены внутренние особенности, специфический порядок полей в сериализации запросов, генерация подписей и обработка внутренних ошибок Kaspi (например, `NotCashierError`, `OrganizationNotCreatedError` и т.д.).

## Особенности
- **Минимум внешних зависимостей**: для работы требуются только `aiohttp` и `cryptography`.
- **4-шаговый сценарий авторизации**:
  1. Инициализация сессии (`init`)
  2. Запрос OTP-кода по номеру телефона (`send_otp`)
  3. Подтверждение OTP-кода (`confirm_otp`)
  4. Завершение регистрации устройства и получение сессионного ключа (`finish`)
- **Управление сессиями и ключами**:
  - Автоматическая генерация EC-ключей (`cryptography`) и хэширование.
  - Сохранение/загрузка сессий, ключей устройства и параметров девайса в JSON-файлы (`device.json`, `keys.json`, `session.json`).

## Установка зависимостей
```bash
pip install aiohttp cryptography
```

## Быстрый старт (Авторизация)

Пример использования клиента для авторизации устройства и сохранения сессии (описан в `main.py`):

```python
import asyncio
import aiohttp
from src.auth.service import AuthClient

async def main():
    async with aiohttp.ClientSession() as session:
        # Инициализация клиента (загрузит существующую сессию или создаст новую)
        auth_client = await AuthClient.from_files(session=session, with_session=False)
        
        # Шаг 1: Инициализация сессии
        meta = await auth_client.init()
        print("Шаг 1 пройден:", meta)

        # Шаг 2: Отправка СМС-кода
        phone = input("Введите номер телефона (например 77071234567): ").strip()
        meta = await auth_client.send_otp(phone)
        print("Шаг 2 пройден:", meta)

        # Шаг 3: Ввод OTP-кода
        code = input("Введите OTP-код из SMS: ").strip()
        meta = await auth_client.confirm_otp(code)
        print("Шаг 3 пройден:", meta)
        
        # Шаг 4: Завершение и сохранение сессии в session.json
        finish_data = await auth_client.finish()
        print("Успешная авторизация! Токен сессии:", finish_data.token_sn)

if __name__ == "__main__":
    asyncio.run(main())
```

## Структура проекта
- `src/auth/schemas.py` — Схемы запросов и ответов.
- `src/auth/service.py` — Клиент авторизации (`AuthClient`).
- `src/auth/keys.py` — Управление ключами и подписью (`Keys`).
- `src/auth/storage.py` — Работа с файлами сессий и ключей (`Storage`).
- `src/auth/transport.py` — HTTP-транспорт.
- `src/auth/validation.py` — Валидация ответов сервера и обработка ошибок.

## Связь
Для связи по вопросам работы библиотеки: Telegram [@SharipovAlan](https://t.me/SharipovAlan)
 
test
