from aiogram.filters.callback_data import CallbackData


class NavigationCallback(CallbackData, prefix='catalog'):
    button: str
    product_index: int
