from aiogram import Router, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from lexicon.lexicon_ru import Lexicon
from keyboards.set_menu import set_admin_menu
from config import load_config
from db.methods import create_cart, get_user_by_telegram_id, create_user

config = load_config()


router = Router()
router.message.filter(lambda message: message.from_user.id in config.tg_bot.admin_ids)


@router.message(CommandStart())
async def start(message: Message, bot: Bot):
    await set_admin_menu(message.from_user.id, bot)
    if (user := get_user_by_telegram_id(telegram_id=message.from_user.id)) == None:
        create_user(
            telegram_id=message.from_user.id,
            telegram_handle=message.from_user.username,
            name='-',
            phone_number='-',
            address='-',
            postal_code='-'
        )
    else:
        if user.cart == None:
            create_cart(user.id)

    await message.answer(Lexicon.Admin.basic__start)


@router.message(Command(commands='spreadsheet'))
async def get_spreadsheet_link(message: Message, state: FSMContext):
    await message.answer('https://docs.google.com/spreadsheets/d/1GhHI6axh7NHRcQYxVTOiLW8cuWXqn02buT9Oo9fflB8')


@router.message(Command(commands='cancel'))
async def cancel(message: Message, state: FSMContext):
    await message.answer('Отмена')
    await state.clear()
    