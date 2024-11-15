from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.callbacks import NavigationCallback, PaymentCallback, ReplyTrackingNumberCallback


def transform_buttons(keys: dict[str, str], product_index: int, description_shown: bool):
    # tranforms dict of {'text': 'callback_data', ...} and product index into valid NavigationCallback
    # description_shown flag is used to control folding and unfolding description
    return [
            InlineKeyboardButton(
                text=text,
                callback_data=NavigationCallback(
                    button=callback_data,
                    product_index=product_index,
                    description_shown=description_shown
                ).pack()
            )
            for text, callback_data in keys.items()
        ]

def create_product_card_keyboard(
    in_cart: int,
    product_index: int,
    catalog_size: int,
    description_button_action: str = 'unfold'
) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    if description_button_action == 'unfold':
        description_shown = False
        kb_builder.row(*transform_buttons(keys={'Читать описание': 'description_unfold'}, product_index=product_index, description_shown=description_shown))
    else:
        description_shown = True
        kb_builder.row(*transform_buttons(keys={'Свернуть описание': 'description_fold'}, product_index=product_index, description_shown=description_shown))
    
    if in_cart > 0:
        keys = {
            '-': '-',
            f'🛒: {in_cart}': 'in_cart',
            '+': '+'
        }
        buttons = transform_buttons(keys=keys, product_index=product_index, description_shown=description_shown)
        kb_builder.row(*buttons, width=3)
    else:
        keys = {
            'Заказать': 'order'
        }
        
        buttons = transform_buttons(keys=keys, product_index=product_index, description_shown=description_shown)
        kb_builder.row(*buttons, width=1)

    keys = {
        '<<': 'prev',
        f'{product_index + 1}/{catalog_size}': 'catalog_state',
        '>>': 'next'
    }

    buttons = transform_buttons(keys=keys, product_index=product_index, description_shown=description_shown)
    kb_builder.row(*buttons, width=3)
    
    return kb_builder.as_markup()


def create_payment_kb(bill_number, order_id) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(InlineKeyboardButton(
        text='Оплачено', 
        callback_data=PaymentCallback(
            bill_number=bill_number,
            order_id=order_id
        ).pack()
    ))
    return kb_builder.as_markup()


def create_inline_kb(width: int,
                     keys: dict,
                     last_btn: dict = None) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    if keys:
        for text, button in keys.items():
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=button
            ))

    kb_builder.row(*buttons, width=width)
    if last_btn:
        kb_builder.row(InlineKeyboardButton(
            text=list(last_btn.keys())[0],
            callback_data=list(last_btn.values())[0]
        ))

    return kb_builder.as_markup()


def create_reply_tracking_number_keyboard(user_telegram_id: int, order_id: int):
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(
            text='Отправить трек-номер', 
            callback_data=ReplyTrackingNumberCallback(
                user_telegram_id=user_telegram_id,
                order_id=order_id
            ).pack()
        )
    )
    return kb_builder.as_markup()