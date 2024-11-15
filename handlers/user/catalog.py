from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_media_photo import InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode


from db.methods import (
    get_products, 
    add_item_to_cart,
    remove_item_from_cart,
    get_cart_by_telegram_id, 
    get_cart_item_by_telegram_id,
    get_user_by_telegram_id,
    update_user
)
from handlers.callbacks import NavigationCallback
from handlers.user.cart import show_cart, delete_cart_message
from db.models import Product
from keyboards.keyboards import create_product_card_keyboard
from config import load_config
from lexicon.lexicon_ru import Lexicon


config = load_config()

router = Router()


async def delete_catalog_message(message, user, bot):
    if user.catalog_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=user.catalog_msg_id)
        except Exception as e:
            pass
        update_user(user.id, catalog_msg_id='')


@router.message(Command(commands='catalog'))
@router.business_message(Command(commands='catalog'))
async def get_catalog(message: Message, bot: Bot, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    await delete_catalog_message(message, user, bot)

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
    
    caption = f'<b>{product.name}</b>\n{product.description[:50]}...\n🔥Актуальная цена: {product.price}₽'
    
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

    description_button_action = 'unfold'

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
            await callback.answer(text=Lexicon.User.process_catalog_navigation__not_enough_product, show_alert=True)
            return
        else:
            user = get_user_by_telegram_id(callback.from_user.id)
            if user.cart_msg_id:
                await show_cart(message=callback.message, bot=bot, state=state, from_catalog=True)
        in_cart = cart_item.quantity
        
    elif callback_data.button == '-':
        cart = get_cart_by_telegram_id(callback.from_user.id)
        remove_item_from_cart(cart_id=cart.id, product_id=product.id)
        cart_item = get_cart_item_by_telegram_id(telegram_id=callback.from_user.id, product_id=product.id)
        if cart_item:
            in_cart = cart_item.quantity
        else:
            in_cart = 0
        user = get_user_by_telegram_id(callback.from_user.id)
        if user.cart_msg_id:
            await show_cart(message=callback.message, bot=bot, state=state, from_catalog=True)
        
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

        caption = f'<b>{product.name}</b>\n{product.description[:50]}...\n🔥Актуальная цена: {product.price}₽'

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
        await show_cart(message=callback.message, bot=bot, state=state, from_catalog=True)
        await callback.answer()
        return
    elif callback_data.button in ['description_fold', 'description_unfold']:
        cart_item = get_cart_item_by_telegram_id(telegram_id=callback.from_user.id, product_id=product.id)
        in_cart = 0
        if cart_item:
            in_cart = cart_item.quantity
            
        if callback_data.button == 'description_unfold':
            caption = f'<b>{product.name}</b>\n{product.description}\n🔥Актуальная цена: {product.price}₽'
            description_button_action = 'fold'
        else:
            caption = f'<b>{product.name}</b>\n{product.description[:50]}...\n🔥Актуальная цена: {product.price}₽'
            description_button_action = 'unfold'

        await callback.message.edit_caption(
            business_connection_id=callback.message.business_connection_id,
            caption=caption,
            parse_mode=ParseMode.HTML
        )

    else:
        await callback.answer()
        return  
    
    reply_markup = create_product_card_keyboard(
        in_cart=in_cart,
        product_index=product_index,
        catalog_size=len(products),
        description_button_action=description_button_action
    )
    try:
        await callback.message.edit_reply_markup(
            business_connection_id=callback.message.business_connection_id,
            reply_markup=reply_markup
        ) 
    except Exception as e:
        print(e)

    await callback.answer()
