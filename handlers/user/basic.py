from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.types.input_media_photo import InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.enums.parse_mode import ParseMode


from db.methods import (
    get_products, 
    add_item_to_cart,
    remove_item_from_cart,
    get_product, 
    get_cart_by_telegram_id, 
    get_cart_items_by_telegram_id,
    get_cart_item_by_telegram_id,
    create_user,
    get_user_by_telegram_id,
    create_order,
    check_and_fix_cart_stock,
    clear_cart,
    update_cart
)
from handlers.user.callbacks import NavigationCallback
from db.models import Product
from keyboards.keyboards import create_inline_kb
from lexicon.lexicon_ru import Lexicon
from keyboards.set_menu import set_user_menu
from keyboards.keyboards import create_product_card_keyboard
from config import load_config
from states.states import FSMGetCatalog


config = load_config()


router = Router()


@router.business_message(CommandStart())
@router.message(CommandStart())
async def start(message: Message, bot: Bot):
    await set_user_menu(message.from_user.id, bot)
    if get_user_by_telegram_id(telegram_id=message.from_user.id) == None:
        create_user(
            telegram_id=message.from_user.id,
            telegram_handle=message.from_user.username,
            name=message.from_user.username,
            phone_number='-',
            address='-',
            postal_code='-'
        )
    
    await message.answer(Lexicon.User.basic__start)
    
    
@router.message(Command(commands='catalog'))
@router.business_message(Command(commands='catalog'))
async def get_catalog(message: Message, bot: Bot, state: FSMContext):
    products = get_products()
    product_index = 0
    # await state.update_data(current_index=current_index)

    product = products[product_index]

    # order_button = 'Заказать'
    cart_item = get_cart_item_by_telegram_id(
        telegram_id=message.from_user.id,
        product_id=product.id
    )
    
    in_cart = 0
    if cart_item:
        in_cart = cart_item.quantity
        
    reply_markup = create_product_card_keyboard(
        in_cart=in_cart,
        product_index=product_index,
        catalog_size=len(products)
    )

    caption = '<b>' + product.name + '</b>' f'\n{product.description}\n🔥Актуальная цена: {product.price}₽'

    await bot.send_photo(
        business_connection_id=message.business_connection_id,
        chat_id=message.chat.id,
        photo=product.picture,
        caption=caption,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

    # await state.update_data(card_msg=card_msg)

    # await state.set_state(FSMGetCatalog.navigate)
    

@router.callback_query(NavigationCallback.filter())
async def process_catalog_navigation(callback: CallbackQuery, callback_data: NavigationCallback, state: FSMContext, bot: Bot):
    products = get_products()
    product_index = callback_data.product_index

    product: Product = products[product_index]

    # item = get_cart_item_by_telegram_id(
    #     telegram_id=callback.from_user.id,
    #     product_id=products[product_index].id
    # )
    # if item:
    #     order_button = f'В корзине: {item.quantity}'

    if callback_data.button in ('order', '+'):
        cart = get_cart_by_telegram_id(callback.from_user.id)
        cart_item = add_item_to_cart(cart_id=cart.id, product_id=product.id)
        if cart_item == None:
            await callback.answer(text='К сожалению, в наличии нет столько единиц выбранного товара', show_alert=True)
            return
        in_cart = cart_item.quantity
    elif callback_data.button == '-':
        cart = get_cart_by_telegram_id(callback.from_user.id)
        remove_item_from_cart(cart_id=cart.id, product_id=product.id)
        cart_item = get_cart_item_by_telegram_id(telegram_id=callback.from_user.id, product_id=product.id)
        if cart_item:
            in_cart = cart_item.quantity
        else:
            in_cart = 0
    elif callback_data.button in ('next', 'prev'):
        if callback_data.button == 'next':
            product_index = (product_index + 1) % len(products)
        elif callback_data.button == 'prev':
            product_index = (product_index - 1) % len(products)
        
        product: Product = products[product_index]
        
        await callback.message.edit_media(
            business_connection_id=callback.message.business_connection_id, 
            media=InputMediaPhoto(media=product.picture)
        )

        caption = '<b>' + product.name + '</b>' f'\n{product.description}\n🔥Актуальная цена: {product.price}₽'
        await callback.message.edit_caption(
            business_connection_id=callback.message.business_connection_id,
            caption=caption,
            parse_mode=ParseMode.HTML
        )

        cart_item = get_cart_item_by_telegram_id(
            telegram_id=callback.from_user.id,
            product_id=product.id
        )
    
        in_cart = 0
        if cart_item:
            in_cart = cart_item.quantity
    elif callback_data.button == 'in_cart':
        await show_cart(message=callback.message, bot=bot, state=state)
        await callback.answer()
        return
    else:
        await callback.answer()
        return  
    
    reply_markup = create_product_card_keyboard(
        in_cart=in_cart,
        product_index=product_index,
        catalog_size=len(products)
    )

    await callback.message.edit_reply_markup(
        business_connection_id=callback.message.business_connection_id,
        reply_markup=reply_markup
    )

    await callback.answer()



@router.message(Command(commands='help'))
@router.business_message(Command(commands='help'))
async def show_help(message: Message, bot: Bot, state: FSMContext):
    await message.answer(Lexicon.User.show_help__)


@router.message(Command(commands='faq'))
@router.business_message(Command(commands='faq'))
async def show_faq(message: Message, bot: Bot, state: FSMContext):
    await message.answer(Lexicon.User.show_faq__)


@router.message(Command(commands='cart'))
@router.business_message(Command(commands='cart'))
async def show_cart(message: Message, bot: Bot, state: FSMContext):
    if not get_user_by_telegram_id(message.chat.id):
        await message.answer('Сначала зарегистрируйтесь с помощью /sign_up')
    elif not get_cart_items_by_telegram_id(message.chat.id):
        await message.answer('Корзина пуста')
    else:
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
        msg.append(f'Общая сумма: {cart.total}р.')
        msg = '\n'.join(msg)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Оформить заказ', callback_data='order')]])
        await message.answer(text=msg, reply_markup=reply_markup)


@router.callback_query(F.data == 'order')
async def process_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    #if not get_cart_items_by_telegram_id(message.chat.id):
    #    await callback.message.answer('Для оформления заказа сначала нужно зарегистрироваться (команда /sign_up)')
    #    await state.clear()
    #    return
        
    check_result = check_and_fix_cart_stock(telegram_id=callback.from_user.id)
    if check_result:
        await callback.answer(
            text='Ввиду отсутствия в наличии из корзины были удалены некоторые позиции:\n\n' + check_result,
            show_alert=True
        )
    await callback.answer()
    cart = get_cart_by_telegram_id(callback.from_user.id)
    delivery_cost = 300 if cart.total < 5000 else 0
    order = create_order(telegram_id=callback.from_user.id, delivery_cost=delivery_cost)
    msg: Message = (await callback.message.answer(f'Совершите оплату по заказу {order.id}'))
    await state.clear()
    # await bot.send_invoice(
    #     title='Title',
    #     description='description',
    #     provider_token=?,
    #     currency='rub',
    #     # photo_url=TIME_MACHINE_IMAGE_URL,
    #     # photo_height=512,  # !=0/None or picture won't be shown
    #     # photo_width=512,
    #     # photo_size=512,
    #     # need_email=True,
    #     # need_phone_number=True,
    #     # need_shipping_address=True,
    #     # is_flexible=True,  # True If you need to set up Shipping Fee
    #     prices=[types.LabeledPrice(label=f'Заказ {order.id}', amount=cart.total)],
    #     start_parameter='start_parameter',
    #     payload='some-invoice-payload-for-our-internal-use'
    # )
