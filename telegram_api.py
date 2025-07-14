from aiogram import Router
from aiogram.types import ChatMemberUpdated
import logging

router = Router()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.my_chat_member()
async def on_my_chat_member_updated(event: ChatMemberUpdated):
    """Функция «ловит» события. Когда в группу добавляют бота, она получает название и ID группы и вызывает функцию,
    которая добавить ID группы в базу данных Seatable"""
    if event.old_chat_member.status in ("left", "kicked") and \
            event.new_chat_member.status in ("member", "administrator", "creator") and \
            event.new_chat_member.user.id == event.bot.id:
        chat_id = event.chat.id
        chat_title = event.chat.title  # Название и id группы, в которую добавили бота

        logger.info(f"Бот добавлен в группу: {chat_title} (ID: {chat_id})")

        # Здесь вызываем функцию записи в базу с названием и ID
        # await write_group_to_db(chat_id, chat_title)
