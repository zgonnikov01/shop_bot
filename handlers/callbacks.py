from aiogram.filters.callback_data import CallbackData


class NavigationCallback(CallbackData, prefix='catalog'):
    button: str
    product_index: int
    description_shown: bool


class PaymentCallback(CallbackData, prefix='payment'):
    bill_number: str
    order_id: int


class ReplyTrackingNumberCallback(CallbackData, prefix='reply_tracking_number'):
    user_telegram_id: int
    order_id: int
