import datetime

from aiogram import Router, Bot
from aiogram.filters import Command, CommandStart, CommandObject, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from lexicon.lexicon_ru import Lexicon
from keyboards.set_menu import set_admin_menu
from config import load_config
from db.methods import create_cart, get_user_by_telegram_id, create_user, clear_cart, create_notification, get_users, get_notifications
from states.states import FSMCreateNotification

config = load_config()


router = Router()
router.message.filter(lambda message: message.from_user.id in config.tg_bot.admin_ids)


@router.message(CommandStart())
async def start(message: Message, bot: Bot, state: FSMContext):
    await set_admin_menu(message.from_user.id, bot)
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
    await message.answer(Lexicon.Admin.basic__start)


@router.message(Command(commands='spreadsheet'))
async def get_spreadsheet_link(message: Message, state: FSMContext):
    await message.answer('https://docs.google.com/spreadsheets/d/1GhHI6axh7NHRcQYxVTOiLW8cuWXqn02buT9Oo9fflB8')


@router.message(Command(commands='cancel'))
async def cancel(message: Message, state: FSMContext):
    await message.answer('Отмена')
    await state.clear()


@router.message(Command(commands='notify'))
async def notify(message: Message, command: CommandObject, bot: Bot, state: FSMContext):
    try:
        if command.args:
            expire_datetime_string = command.args
        else:
            expire_datetime_string = None
        await state.update_data(expire_datetime_string=expire_datetime_string)
        await state.set_state(FSMCreateNotification.get_notification_message)
        await message.answer('Отправьте уведомление вместе с картинкой (одним сообщением)')
    except Exception as e:
        await message.answer('Ошибка')
        print(e)


@router.message(StateFilter(FSMCreateNotification.get_notification_message))
async def notify_get_notification_message(message: Message, bot: Bot, state: FSMContext):
    try:
        expire_datetime_string = (await state.get_data())['expire_datetime_string']
        if expire_datetime_string:
            expire_datetime = datetime.datetime.fromisoformat(expire_datetime_string)
        else:
            expire_datetime=None
        text = message.caption if message.caption else message.text
        media = message.photo[-1].file_id if message.photo else ''
        notification = create_notification(
            text=text,
            media=media,
            expire_datetime=expire_datetime
        )
        users = get_users()
        for user in users:
            try:
                if message.photo:
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
            except Exception as e:
                print(e)
        await message.answer(f'Объявление id{notification.id} отправлено пользователям')
    except Exception as e:
        print(e)
        await message.answer('Ошибка')
    await state.clear()

