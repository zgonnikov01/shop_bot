from aiogram import Router, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


from db.methods import (
    create_cart,
    create_user,
    clear_cart,
    get_user_by_telegram_id
)
from lexicon.lexicon_ru import Lexicon
from keyboards.set_menu import set_user_menu
from config import load_config


config = load_config()

router = Router()


@router.message(CommandStart())
async def start(message: Message, bot: Bot):
    await set_user_menu(message.from_user.id, bot)
    if user := get_user_by_telegram_id(telegram_id=message.from_user.id) == None:
        user = create_user(
            telegram_id=message.from_user.id,
            telegram_handle=message.from_user.username,
            name='-',
            phone_number='-',
            address='-',
            postal_code='-'
        )
        create_cart(user.id)
    else:
        if user.cart == None:
            create_cart(user.id)
        else:
            clear_cart(user.cart.id)
    
    await message.answer(Lexicon.User.basic__start)
    

@router.message(Command(commands='help'))
async def show_help(message: Message, bot: Bot, state: FSMContext):
    await message.answer(Lexicon.User.show_help__)


@router.message(Command(commands='faq'))
async def show_faq(message: Message, bot: Bot, state: FSMContext):
    await message.answer(Lexicon.User.show_faq__)


@router.message(Command(commands='cancel'))
async def cancel(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
