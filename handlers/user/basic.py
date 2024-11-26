from aiogram import Router, Bot
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


from db.methods import (
    create_cart,
    create_user,
    clear_cart,
    get_user_by_telegram_id,
    get_notifications,
    get_user_data_by_tg_id_fancy
)
from states.states import FSMSendFeedback
from lexicon.lexicon_ru import Lexicon
from keyboards.set_menu import set_user_menu
from config import load_config


config = load_config()

router = Router()


@router.message(Command(commands='feedback'))
async def share_feedback(message: Message, state: FSMContext):
    await message.answer(Lexicon.User.send_feedback__get_message)
    await state.set_state(FSMSendFeedback.get_message)


@router.message(StateFilter(FSMSendFeedback.get_message))
async def share_feedback_proceed(message: Message, bot: Bot, state: FSMContext):
    msg = await bot.copy_message(
        message_id=message.message_id,
        chat_id=-1002473615887,
        message_thread_id=441,
        from_chat_id=message.from_user.id,
    )
    await bot.send_message(
        text=get_user_data_by_tg_id_fancy(user_tg_id=message.from_user.id),
        chat_id=-1002473615887,
        message_thread_id=441,
        reply_to_message_id=msg.message_id,
        parse_mode='HTML'
    )
    await message.answer(Lexicon.User.send_feedback__success)
    await state.clear()


@router.message(CommandStart())
async def start(message: Message, bot: Bot, state: FSMContext):
    await set_user_menu(message.from_user.id, bot)
    user = get_user_by_telegram_id(telegram_id=message.from_user.id)
    if user == None:
        user = create_user(
            telegram_id=message.from_user.id,
            telegram_handle=message.from_user.username,
            name='-',
            phone_number='-',
            country='-',
            address='-',
            postal_code='-'
        )
        notifications = get_notifications()
        for notification in notifications:
            if notification.media != '':
                await bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=notification.media,
                    caption=notification.text
                )
            else:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=notification.text
                )
    else:
        if user.cart == None:
            create_cart(user.id)
        else:
            clear_cart(user.cart.id)
    
    await state.clear()
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
