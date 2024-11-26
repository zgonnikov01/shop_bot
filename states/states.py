from aiogram.fsm.state import StatesGroup, State


# class FSMCreateProduct(StatesGroup):
#     set_name = State()
#     set_picture = State()
#     set_description = State()
#     set_categories = State()
#     set_stock = State()
#     finish = State()


class FSMEditProducts(StatesGroup):
    select_product = State()
    select_field = State()
    edit_field = State()
    save = State()


class FSMUpdateCatalog(StatesGroup):
    set_pictures = State()


class FSMGetCatalog(StatesGroup):
    navigate = State()


class FSMSignUp(StatesGroup):
    get_full_name = State()
    get_number = State()
    get_country = State()
    get_address = State()
    get_postal_code = State()


class FSMPayment(StatesGroup):
    confirm = State()


class FSMAddTrackingNumber(StatesGroup):
    request_number = State()


class FSMCreateNotification(StatesGroup):
    get_notification_message = State()


class FSMSendFeedback(StatesGroup):
    get_message = State()

