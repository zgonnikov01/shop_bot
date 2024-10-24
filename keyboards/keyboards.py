from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.user.callbacks import NavigationCallback


def transform_buttons(keys, product_index):
    return [
            InlineKeyboardButton(
                text=text,
                callback_data=NavigationCallback(
                    button=callback_data,
                    product_index=product_index
                ).pack()
            )
            for text, callback_data in keys.items()
        ]

def create_product_card_keyboard(
    in_cart: int,
    product_index: int,
    catalog_size: int
) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    if in_cart > 0:
        keys = {
            '-': '-',
            f'🛒: {in_cart}': 'in_cart',
            '+': '+'
        }
        buttons = transform_buttons(keys=keys, product_index=product_index)
        kb_builder.row(*buttons, width=3)
    else:
        keys = {
            'Заказать': 'order'
        }
        
        buttons = transform_buttons(keys=keys, product_index=product_index)
        kb_builder.row(*buttons, width=1)

    keys = {
        '<<': 'prev',
        f'{product_index + 1}/{catalog_size}': 'catalog_state',
        '>>': 'next'
    }

    buttons = transform_buttons(keys=keys, product_index=product_index)
    kb_builder.row(*buttons, width=3)
    
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
