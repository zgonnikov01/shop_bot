from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.types.input_media_photo import InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from db.methods import create_user, update_user, get_user_by_telegram_id, get_user_data_by_tg_id_fancy
from db.models import User
from keyboards.keyboards import create_inline_kb, create_country_select_kb
from lexicon.lexicon_ru import Lexicon
from keyboards.set_menu import set_user_menu
from config import load_config
from states.states import FSMSignUp


class NavigationCallback(CallbackData, prefix='catalog'):
    button: str
    product_index: int


config = load_config()


router = Router()


@router.callback_query(F.data == 'sign_up')
async def sign_up_from_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.delete_message(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id
    )
    msg = await callback.message.answer(Lexicon.User.sign_up__get_full_name)
    await state.update_data(msg_id_sign_up_1=msg.message_id)
    await state.set_state(FSMSignUp.get_full_name)
    await callback.answer()


@router.message(Command(commands='sign_up'))
async def sign_up(message: Message, bot: Bot, state: FSMContext):
    await message.delete()
    msg = await message.answer(Lexicon.User.sign_up__get_full_name)
    await state.update_data(msg_id_sign_up_1=msg.message_id)
    await state.set_state(FSMSignUp.get_full_name)


@router.message(StateFilter(FSMSignUp.get_full_name))
async def sign_up_get_full_name(message: Message, bot: Bot, state: FSMContext):
    msg_id = (await state.get_data())['msg_id_sign_up_1']
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=msg_id
    )
    await message.delete()
    await state.update_data(full_name=message.text)
    msg = await message.answer(Lexicon.User.sign_up__get_number)
    await state.update_data(msg_id_sign_up_2=msg.message_id)
    await state.set_state(FSMSignUp.get_number)




@router.message(StateFilter(FSMSignUp.get_number))
async def sign_up_get_address(message: Message, bot: Bot, state: FSMContext):
    msg_id = (await state.get_data())['msg_id_sign_up_2']
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=msg_id
    )
    await message.delete()
    try:
        #trimmed = message.text.replace(' ', '').replace('-', '')
        #if len(trimmed) != 11:
        #    raise Exception
        #number = '+7' + trimmed[-10:]

        number = message.text
        await state.update_data(number=number)

        reply_markup = create_country_select_kb()
        msg = await message.answer(
            text=Lexicon.User.sign_up__get_country,
            reply_markup=reply_markup
        )
        await state.set_state(FSMSignUp.get_country)
        await state.update_data(msg_id_sign_up_3=msg.message_id)

    except Exception as e:
        print(e)
        await message.answer(Lexicon.User.sign_up__incorrect_number)


@router.callback_query(StateFilter(FSMSignUp.get_country))
async def sign_up_get_country(callback: CallbackQuery, bot: Bot, state: FSMContext):
    msg_id = (await state.get_data())['msg_id_sign_up_3']
    await bot.delete_message(
        chat_id=callback.from_user.id,
        message_id=msg_id
    )
    try:
        if callback.data == 'other':
            await callback.message.answer(Lexicon.User.sign_up__get_country_fail)
            await callback.message.answer(Lexicon.User.sign_up__abort)
            await state.clear()
        else:
            await state.update_data(country=callback.data)
            await state.set_state(FSMSignUp.get_address)
            msg = await callback.message.answer(Lexicon.User.sign_up__get_address)
            await state.update_data(msg_id_sign_up_4=msg.message_id)
        await callback.answer()
    except Exception as e:
        print(e)


@router.message(StateFilter(FSMSignUp.get_address))
async def sign_up_get_postal_code(message: Message, bot: Bot, state: FSMContext):
    msg_id = (await state.get_data())['msg_id_sign_up_4']
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=msg_id
    )
    await message.delete()
    await state.update_data(address=message.text)
    msg = await message.answer(Lexicon.User.sign_up__get_postal_code)
    await state.update_data(msg_id_sign_up_5=msg.message_id)
    await state.set_state(FSMSignUp.get_postal_code)


@router.message(StateFilter(FSMSignUp.get_postal_code))
async def sign_up_get_address(message: Message, bot: Bot, state: FSMContext):
    postal_code = message.text
    data = await state.get_data()
    user = get_user_by_telegram_id(message.from_user.id)
    msg_id = (await state.get_data())['msg_id_sign_up_5']
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=msg_id
    )
    await message.delete()
    msg = await message.answer('Обработка...')
    if user:
        update_user(
            user_id=user.id,
            telegram_id=message.from_user.id,
            telegram_handle=message.from_user.username,
            name=data['full_name'],
            phone_number=data['number'],
            country=data['country'],
            address=data['address'],
            postal_code=postal_code
        )
    else:
        create_user(
            telegram_id=message.from_user.id,
            telegram_handle=message.from_user.username,
            name=data['full_name'],
            phone_number=data['number'],
            country=data['country'],
            address=data['address'],
            postal_code=postal_code
        )
    #await message.answer(Lexicon.User.sign_up__success)
    await msg.delete()
    await message.answer(
        Lexicon.User.sign_up__success_base + get_user_data_by_tg_id_fancy(user_tg_id=user.telegram_id, minimize=True)
    )
    #if 'sign_up_from_order_msg_id' in data:
    #    reply_markup = InlineKeyboardMarkup(
    #        inline_keyboard = [
    #            [InlineKeyboardButton(text='Вернуться к заказу', callback_data='sign_up')],
    #            [InlineKeyboardButton(text='Отмена', callback_data='sign_up__cancel_return_to_order')]
    #        ]
    #    )
    #    await bot.message(
    #        text=Lexicon.User.sign_up__success_return_to_order,
    #        reply_markup=reply_markup
    #    )
    await state.clear()


@router.callback_query(F.data == 'sign_up__cancel_return_to_order')
async def sign_up__cancel_return_to_order(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    try:
        await bot.delete_message(
            chat_id=callback.from_user.id,
            message_id=data['sign_up_from_order_msg_id']
        )
    except Exception as e:
        print(e)
    await state.clear()
