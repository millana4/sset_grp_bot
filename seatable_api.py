import json
import time
import aiohttp
import logging

from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

# Глобальный кэш токена
_token_cache: Dict[str, Optional[Dict]] = {
    "token_data": None,
    "timestamp": 0
}
_TOKEN_TTL = 172800  # время жизни токена в секундах — 48 часов


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
    now = time.time()
    cached = _token_cache["token_data"]
    cached_time = _token_cache["timestamp"]

    if cached and (now - cached_time) < _TOKEN_TTL:
        return cached

    url = "https://cloud.seatable.io/api/v2.1/dtable/app-access-token/"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {Config.SEATABLE_API_TOKEN}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                token_data = await response.json()
                logger.debug("Base token successfully obtained and cached")

                # Обновляем кэш
                _token_cache["token_data"] = token_data
                _token_cache["timestamp"] = now

                return token_data

    except aiohttp.ClientError as e:
        logger.error(f"API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

    return None


async def write_group_to_db(chat_id: int, chat_title: str):
    token_data = await get_base_token()
    if not token_data:
        logger.error("❌ Не удалось получить токен SeaTable")
        return

    access_token = token_data["access_token"]
    dtable_uuid = token_data["dtable_uuid"]
    base_url = token_data["dtable_server"].rstrip("/")
    table_name = Config.SEATABLE_GROUPS_TABLE_ID

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            # Формируем SQL-запрос для обновления
            sql_url = f"{base_url}/api/v2/dtables/{dtable_uuid}/sql"
            sql_query = f"""
                UPDATE `{table_name}` 
                SET `tg_grp_id` = ? 
                WHERE `Name` = ?
            """

            sql_payload = {
                "sql": sql_query,
                "parameters": [str(chat_id), chat_title],
                "convert_keys": False  # Работаем с ключами столбцов
            }

            logger.debug(f"Отправка SQL-запроса: {sql_query} с параметрами: {[str(chat_id), chat_title]}")

            async with session.post(sql_url, headers=headers, json=sql_payload) as response:
                response_text = await response.text()

                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Успешно обновлено через SQL API: {result}")
                else:
                    logger.error(f"❌ Ошибка SQL-запроса: {response.status} - {response_text}")

        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка при работе с API SeaTable: {e}")
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")


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