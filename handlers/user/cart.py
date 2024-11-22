from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext


from db.methods import (
    clear_cart,
    get_cart_items_by_telegram_id_fancy,
    get_order_items_for_lifepay,
    get_order,
    get_order_items_names,
    get_product, 
    get_cart_by_telegram_id, 
    get_cart_items_by_telegram_id,
    get_user_by_telegram_id,
    create_order,
    check_and_fix_cart_stock,
    get_user_data_by_tg_id_fancy,
    update_cart,
    update_order,
    update_user
)
from handlers.callbacks import PaymentCallback
from keyboards.keyboards import create_payment_kb, create_reply_tracking_number_keyboard
from lexicon.lexicon_ru import Lexicon
from payments.payments import (
    create_bill,
    get_bill_status
)
from config import load_config
from sheets.orders import update_order_in_sheet
from states.states import FSMPayment
from keyboards.keyboards import create_inline_kb


config = load_config()

router = Router()


async def delete_cart_message(message, user, bot):
    if user.cart_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=user.cart_msg_id)
        except Exception as e:
            pass
        update_user(user.id, cart_msg_id='')


@router.message(Command(commands='cart'))
@router.business_message(Command(commands='cart'))
async def show_cart(message: Message, bot: Bot, state: FSMContext, from_catalog=False):
    if not get_user_by_telegram_id(message.chat.id):
        await message.answer('Сначала зарегистрируйтесь с помощью /sign_up')
    elif not get_cart_items_by_telegram_id(message.chat.id):
        try:
            user = get_user_by_telegram_id(message.chat.id)
            await delete_cart_message(message, user, bot)
        except Exception as e:
            print(e)
        sent_msg = await message.answer(Lexicon.User.__cart_is_empty)
        update_user(user.id, cart_msg_id=sent_msg.message_id)
    else:
        user = get_user_by_telegram_id(message.chat.id)
        await delete_cart_message(message, user, bot)

        cart_items = get_cart_items_by_telegram_id(message.chat.id)
        msg = []
        current_total = 0
        for cart_item in cart_items:
            product = get_product(cart_item.product_id)
            price = product.price
            quantity = cart_item.quantity
            current_total += quantity * price
            msg.append(
            f'{product.name}: {str(quantity)} * {str(price)}р. = {str(quantity * price)}р.'
            )
        cart = get_cart_by_telegram_id(message.chat.id)
        update_cart(cart_id=cart.id, total=current_total)

        if cart.total < 5000:
            delivery_cost = 300
        else:
            delivery_cost = 0

        msg.append(f'Стоимость доставки по РФ: {delivery_cost}р.')

        # msg.append(f'Стоимость доставки*: {delivery_cost}р.')
        # TODO Рассчитать стоимость доставки

        msg.append(f'Общая сумма: {cart.total + delivery_cost}р.')

        # Просим пользователя проверить свои данные

        msg = '\n'.join(msg)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Оформить заказ', callback_data='order_check_data')]])
        sent_msg = await message.answer(text=msg, reply_markup=reply_markup)
        update_user(user.id, cart_msg_id=sent_msg.message_id)
    if not from_catalog:
        await message.delete()


@router.callback_query(F.data == 'order_check_data')
async def process_order__check_data(callback: CallbackQuery, state: FSMContext, bot: Bot):
    msg = Lexicon.User.process_order__check_data + get_user_data_by_tg_id_fancy(user_tg_id=callback.from_user.id, minimize=True)
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Редактировать мои данные', callback_data='sign_up')],
            [InlineKeyboardButton(text='Оформить заказ', callback_data='order')]
        ]
    )

    await callback.message.answer(text=msg, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data == 'order')
async def process_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user = get_user_by_telegram_id(callback.from_user.id)
    print(user)
    if any([x == None or x == '-' for x in [user.name, user.phone_number, user.address, user.postal_code]]):
        await callback.answer(
            text=Lexicon.User.process_order__,
            show_alert=True
        )
        await state.clear()
        return
    elif not get_cart_items_by_telegram_id(callback.from_user.id):
        try:
            await delete_cart_message(callback.message, user, bot)
        except Exception as e:
            print(e)
        await callback.answer(
            text=Lexicon.User.__cart_is_empty,
            show_alert=True
        )
        await state.clear()
        return

    check_result = check_and_fix_cart_stock(telegram_id=callback.from_user.id)
    if check_result:
        await callback.answer(
            text=Lexicon.User.process_order__check_stock + check_result,
            show_alert=True
        )

    user = get_user_by_telegram_id(callback.from_user.id)
    cart = get_cart_by_telegram_id(callback.from_user.id)
    delivery_cost = 350 if cart.total < 5000 else 0
    order = create_order(telegram_id=callback.from_user.id, delivery_cost=delivery_cost)
    description = get_order_items_for_lifepay(order_id=order.id)
    try:

        bill = create_bill(
            amount=order.total,
            description=description,
            customer_phone=user.phone_number.strip('+').replace(' ', '')
        )

        print(bill)

        if bill['code'] != 0:
            raise Exception
        payment_url = bill['data']['paymentUrl']
        
        await state.set_state(FSMPayment.confirm)

        print(bill['data']['number'])
        
        await callback.answer()

        msg = await callback.message.answer(
            f'Совершите оплату по заказу:\n{payment_url}\nПосле оплаты нажмите на кнопку',
            reply_markup=create_payment_kb(
                bill_number=str(bill['data']['number']),
                order_id=order.id
            )
        )
        
        await delete_cart_message(callback.message, user, bot)

    except Exception as e:
        print(e)
        msg: Message = (await callback.message.answer('Извините, что-то пошло не так. Пожалуйста, проверьте ваши данные на соответствие шаблону, используя команду /sign_up'))
        await state.clear()
        await callback.answer()


@router.callback_query(PaymentCallback.filter())
async def confirm_payment(callback: CallbackQuery, callback_data: PaymentCallback, state: FSMContext, bot: Bot):
    bill_number = callback_data.bill_number
    try:
        bill_status = get_bill_status(bill_number)['data'][bill_number]['status']
        print(type(bill_status))
        user_id = callback.from_user.id
        order_details = get_cart_items_by_telegram_id_fancy(user_id)
        order_id = callback_data.order_id
        payment_msg_id = callback.message.message_id
        if bill_status == 10 or True:
            # Cообщаем пользователю, что заказ успешно оплачен
            await callback.message.answer(
                f'Заказ {order_id} создан и оплачен. Когда он будет передан в доставку, Вам будет отправлен трек-номер для отслеживания' +
                '\n\nСостав заказа:\n' + 
                order_details
            )
            
            # Удаляем сообщение со ссылкой на оплату
            await bot.delete_message(
                chat_id = user_id,
                message_id = payment_msg_id
            )

            # Сообщаем админу о заказе
            order_details_for_admin = \
                f'Заказ {order_id}\n\nСостав заказа:\n{order_details}\n\nДанные клиента:\n{get_user_data_by_tg_id_fancy(user_id)}'
        
            markup = create_reply_tracking_number_keyboard(user_telegram_id=user_id, order_id=order_id)

            admin_id = config.tg_bot.admin_ids[0]

            await bot.send_message(
                chat_id=admin_id,
                text=order_details_for_admin,
                parse_mode='HTML',
                reply_markup=markup
            )

            # Обновляем статус заказа в бд
            update_order(order_id=order_id, status='Оплачен')

            # Обновляем данные в гугл-таблице
            update_order_in_sheet(
                order=get_order(order_id),
                order_items_names=get_order_items_names(order_id=order_id)
            )
            
            # Очищаем корзину
            clear_cart(cart_id=get_cart_by_telegram_id(callback.from_user.id).id)

            await state.clear()
        else:
            await callback.answer(
                text='Платёж ещё не обработан. Если вы оплатили, подождите несколько минут и попробуйте снова',
                show_alert=True
            )
            await state.clear()
    except Exception as e:
        print(e)
        await callback.answer('Ошибка')
        
    await callback.answer()
    # callback.message.answer(get_bill_status(bill_number))


@router.message(Command(commands=['check']))
async def check_state(message: Message, state: FSMContext, bot: Bot):
    await message.answer('admin:', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Написать админу', url='tg://user?id=449769108')]]))
