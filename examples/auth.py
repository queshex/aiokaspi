import asyncio
import aiohttp

from aiokaspi.auth.service import AuthClient


# Just for checking git
async def main():
    async with aiohttp.ClientSession() as session:
        auth_client = await AuthClient.from_files(session=session, with_session=False)

        # Шаг 1: Инициализация
        data = await auth_client.init()
        print("Step 1 (init) OK:", data)

        # Шаг 2: Отправка OTP
        phone = input("Введите номер телефона (например 77071234567): ").strip()
        data = await auth_client.send_otp(phone)
        print("Step 2 (send_otp) OK:", data)

        # Шаг 3: Подтверждение OTP
        code = input("Введите OTP-код из SMS: ").strip()
        data = await auth_client.confirm_otp(code)
        print("Step 3 (confirm_otp) OK:", data)
        finish_data = await auth_client.finish()
        print("Step 4 (finish) OK:", finish_data)


if __name__ == "__main__":
    asyncio.run(main())
