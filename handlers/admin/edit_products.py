from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.types.chat import Chat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Text, Italic
from datetime import datetime

from states.states import FSMEditProducts
from db.methods import create_product, update_product, get_product, get_products
from keyboards.keyboards import create_inline_kb
from lexicon.lexicon_ru import Lexicon
from config import load_config


config = load_config()


router = Router()
router.message.filter(lambda message: message.from_user.id in config.tg_bot.admin_ids)


@router.message(Command(commands='cancel'))
async def cancel(message: Message, state: FSMContext):
    await message.answer('Отмена')
    await state.clear()


@router.message(Command(commands='edit_products'))
async def edit_goods(message: Message, state: FSMContext):
    products = get_products()
    buttons = {str(product.name): str(product.id) for product in products}
    buttons.update({'Отмена': 'cancel'})
    markup = create_inline_kb(1, buttons)

    msg: Message = await message.answer(Lexicon.Admin.edit_products__select_product, reply_markup=markup)

    await state.update_data(
        msg_id=msg.message_id,
        msg_date=msg.date.isoformat(),
        msg_chat_id=msg.chat.id,
        msg_chat_type=msg.chat.type
    )

    await state.set_state(FSMEditProducts.select_product)


@router.callback_query(StateFilter(FSMEditProducts.select_product))
async def edit_goods__select_field(callback: CallbackQuery, state: FSMContext, bot: Bot):
    msg_id = (await state.get_data())['msg_id']
    msg_date = datetime.fromisoformat((await state.get_data())['msg_date'])
    msg_chat = Chat(id=(await state.get_data())['msg_chat_id'], type=(await state.get_data())['msg_chat_type'])

    msg: Message = Message(
        message_id=msg_id,
        date=msg_date,
        chat=msg_chat
    ).as_(bot)

    if callback.data == 'cancel':
        await msg.delete()
        await state.clear()
        print(await state.get_state())
    else:
        product = get_product(product_id=callback.data)
        buttons = {f'{field_name}: {field_value}': field_name for field_name, field_value in product.__dict__.items()}
        buttons.update({'Отмена': 'cancel'})
        markup = create_inline_kb(1, buttons)

        await msg.edit_text(
            **(Text(Italic(product.name), '\n', Lexicon.Admin.edit_products__select_field)).as_kwargs()
        )
        await msg.edit_reply_markup(
            reply_markup=markup
        )
    await state.set_state(FSMEditProducts.select_field)