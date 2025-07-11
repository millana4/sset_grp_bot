import aiohttp
import logging

from typing import List, Dict, Optional

from config import Config

logger = logging.getLogger(__name__)

async def get_base_token() -> Optional[Dict]:
    """
    Получает временный токен для синхронизации по Апи.
    Возвращает словарь:
    {
        "app_name": "ssetuser",
        "access_token": "some_token_string",
        "dtable_uuid": "4cacfb1a-7d69-45ec-b181-952b913e1483",
        "workspace_id": 82533,
        "dtable_name": "users_sset-grp",
        "use_api_gateway": true,
        "dtable_server": "https://cloud.seatable.io/api-gateway/"
    }
    """
    url = "https://cloud.seatable.io/api/v2.1/dtable/app-access-token/"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {Config.SEATABLE_API_TOKEN}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()  # Вызовет исключение для 4XX/5XX статусов
                token_data = await response.json()
                logger.debug("Base token successfully obtained")
                return token_data

    except aiohttp.ClientError as e:
        logger.error(f"API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

    return None


async def get_last_uid(email: str) -> str | None:
    """Получает последний обработанный UID письма в ящике"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user:
                logger.debug(f"Найден last_uid для {email}: {user.last_uid}")
                return user.last_uid
            logger.warning(f"Пользователь с email {email} не найден")
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении last_uid: {e}")
        raise


async def update_last_uid(email: str, last_uid: str) -> None:
    """Обновляет последний обработанный UID для ящика"""
    try:
        async with AsyncSessionLocal() as session:
            # Получаем пользователя и блокируем запись для обновления
            result = await session.execute(
                select(User)
                .where(User.email == email)
                .with_for_update()
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"Пользователь с email {email} не найден")
                return

            old_uid = user.last_uid
            user.last_uid = last_uid

            # Явно добавляем пользователя в сессию
            session.add(user)
            await session.commit()
            logger.info(f"UID обновлён для {email}: {old_uid} -> {last_uid}")

    except Exception as e:
        logger.error(f"Ошибка при обновлении last_uid: {e}")
        if 'session' in locals():
            await session.rollback()
        raise