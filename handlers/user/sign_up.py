from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.types.input_media_photo import InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from db.methods import create_user, update_user, get_user_by_telegram_id
from db.models import User
from keyboards.keyboards import create_inline_kb
from lexicon.lexicon_ru import Lexicon
from keyboards.set_menu import set_user_menu
from config import load_config
from states.states import FSMSignUp


class NavigationCallback(CallbackData, prefix='catalog'):
    button: str
    product_index: int


config = load_config()


router = Router()

@router.message(Command(commands='sign_up'))
@router.business_message(Command(commands='sign_up'))
async def sign_up(message: Message, bot: Bot, state: FSMContext):
    await message.answer(Lexicon.User.sign_up__get_full_name)
    await state.set_state(FSMSignUp.get_full_name)


@router.message(StateFilter(FSMSignUp.get_full_name))
@router.business_message(StateFilter(FSMSignUp.get_full_name))
async def sign_up_get_full_name(message: Message, bot: Bot, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer(Lexicon.User.sign_up__get_number)
    await state.set_state(FSMSignUp.get_number)


@router.message(StateFilter(FSMSignUp.get_number))
@router.business_message(StateFilter(FSMSignUp.get_number))
async def sign_up_get_address(message: Message, bot: Bot, state: FSMContext):
    await state.update_data(number=message.text)
    await message.answer(Lexicon.User.sign_up__get_address)
    await state.set_state(FSMSignUp.get_address)


@router.message(StateFilter(FSMSignUp.get_address))
@router.business_message(StateFilter(FSMSignUp.get_address))
async def sign_up_get_postal_code(message: Message, bot: Bot, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer(Lexicon.User.sign_up__get_postal_code)
    await state.set_state(FSMSignUp.get_postal_code)


@router.message(StateFilter(FSMSignUp.get_postal_code))
@router.business_message(StateFilter(FSMSignUp.get_postal_code))
async def sign_up_get_address(message: Message, bot: Bot, state: FSMContext):
    postal_code = message.text
    data = await state.get_data()
    user = get_user_by_telegram_id(message.from_user.id)
    if user:
        update_user(
            user_id=user.id,
            telegram_id=message.from_user.id,
            telegram_handle=message.from_user.username,
            name=data['full_name'],
            phone_number=data['number'],
            address=data['address'],
            postal_code=postal_code
        )
    else:
        create_user(
            telegram_id=message.from_user.id,
            telegram_handle=message.from_user.username,
            name=data['full_name'],
            phone_number=data['number'],
            address=data['address'],
            postal_code=postal_code
        )
    await message.answer(Lexicon.User.sign_up__success)
    await state.clear()
