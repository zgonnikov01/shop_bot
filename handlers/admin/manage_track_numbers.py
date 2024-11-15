from aiogram import Router, Bot
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from handlers.callbacks import ReplyTrackingNumberCallback
from sheets.orders import update_order_in_sheet
from states.states import FSMAddTrackingNumber
from lexicon.lexicon_ru import Lexicon
from keyboards.set_menu import set_admin_menu
from config import load_config
from db.methods import create_cart, get_order_items_fancy, get_order, get_order_items_names, get_user_by_telegram_id, create_user, get_user_data_by_tg_id_fancy, update_order

config = load_config()


router = Router()
router.message.filter(lambda message: message.from_user.id in config.tg_bot.admin_ids)


@router.callback_query(ReplyTrackingNumberCallback.filter())
async def add_track_number__request_number(callback: CallbackQuery, callback_data: ReplyTrackingNumberCallback, state: FSMContext, bot: Bot):
    reply_message = await callback.message.reply(Lexicon.Admin.add_track_number__request_number)
    await state.update_data(
        original_order_message_id=callback.message.message_id,
        user_telegram_id=callback_data.user_telegram_id,
        order_id=callback_data.order_id,
        reply_message_id=reply_message.message_id
    )
    await state.set_state(FSMAddTrackingNumber.request_number)
    await callback.answer()


@router.message(StateFilter(FSMAddTrackingNumber.request_number))
async def add_track_number__receive_number(message: Message, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    
    original_order_message_id = state_data['original_order_message_id']
    user_telegram_id = state_data['user_telegram_id']
    order_id = state_data['order_id']
    reply_message_id = state_data['reply_message_id']
    
    user_id = message.from_user.id # Тут юзер - это админ

    # Изменяем исходное сообщение с кнопкой "Добавить трек-номер"

    order_details = get_order_items_fancy(order_id)

    # Обновляем статус заказа в бд
    update_order(order_id=order_id, status='Передан в доставку', tracking_number=message.text)

    # Обновляем данные в гугл-таблице
    update_order_in_sheet(
        order=get_order(order_id),
        order_items_names=get_order_items_names(order_id=order_id)
    )

    await bot.edit_message_text(
        text=f'Заказ {order_id} ✅\n\nТрек-номер: {message.text}\n\nСостав заказа:\n{order_details}\n\nДанные клиента:\n{get_user_data_by_tg_id_fancy(user_telegram_id)}',
        chat_id=user_id,
        message_id=original_order_message_id,
        reply_markup=None,
        parse_mode='HTML'
    )

    # Пишем пользователю

    await bot.send_message(
        chat_id=user_telegram_id,
        text=f'Ваш заказ {order_id} отправлен.\n\nСостав заказа:\n{order_details}\n\nДля отслеживания используйте трек-номер: {message.text}',
        parse_mode='HTML'
    )

    # Удаляем ненужные сообщения: от пользователя

    await message.delete()

    # Удаляем ненужные сообщения: от бота

    await bot.delete_message(
        chat_id=user_id,
        message_id=reply_message_id,
    )

    await state.clear()