from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

import sheets.products
from states.states import FSMUpdateCatalog
from db.models import Product
from db.methods import create_product, update_product, get_products, get_product
from keyboards.keyboards import create_inline_kb
from lexicon.lexicon_ru import Lexicon
from config import load_config


config = load_config()


router = Router()
router.message.filter(lambda message: message.from_user.id in config.tg_bot.admin_ids)


# @router.message(Command(commands='add_product'))
# async def add_good(message: Message, state: FSMContext):
#     await message.answer(Lexicon.Admin.add_goods__set_name)
#     await state.set_state(FSMCreateProduct.set_name)


# @router.message(StateFilter(FSMCreateProduct.set_name))
# async def add_good_set_name(message: Message, state: FSMContext):
#     name = message.text
#     await state.update_data(name=name)
#     create_product(name=name)

#     await message.answer()
#     await state.set_state(FSMCreateProduct.set_description)


# @router.message(StateFilter(FSMCreateProduct.set_description))
# async def add_good_set_description(message: Message, state: FSMContext):
#     product_name = (await state.get_data())['name']
#     description = message.text
#     update_product(product_name, {'description': description})

#     await message.answer(Lexicon.Admin.add_goods__set_description)
#     await state.set_state(FSMCreateProduct.set_category)


# @router.message(StateFilter(FSMCreateProduct.set_category))
# async def add_good_set_category(message: Message, state: FSMContext):
#     product_name = (await state.get_data())['name']
#     category = message.text
#     update_product(product_name, {'category': category})

#     await message.answer(Lexicon.Admin.add_goods__set_stock)
#     await state.set_state(FSMCreateProduct.set_stock)


# @router.message(StateFilter(FSMCreateProduct.set_stock))
# async def add_good_set_stock(message: Message, state: FSMContext):
#     product_name = (await state.get_data())['name']
#     stock = int(message.text)
#     update_product(product_name, {'stock': stock})

    
#     await message.answer(Lexicon.Admin.add_goods__set_picture)
#     await state.set_state(FSMCreateProduct.set_picture)


# @router.message(StateFilter(FSMCreateProduct.set_picture), F.photo)
# async def add_good_set_picture(message: Message, state: FSMContext):
#     product_name = (await state.get_data())['name']
#     picture = message.photo[-1].file_id
#     update_product(product_name, {'picture': picture})
    
#     await message.answer(Lexicon.Admin.add_goods__success)
#     await state.clear()


@router.message(Command(commands='update_catalog'))
async def update_catalog(message: Message, state: FSMContext):
    products_to_be_updated = []
    update_required = False
    try:
        products_: list[dict] = sheets.products.get_products()
        for product_ in products_:
            if product_['id'] != '' and get_product(product_['id']) != None:
                product = update_product(
                    product_id=product_['id'],
                    name=product_['name'],
                    description=product_['description'],
                    categories=product_['categories'],
                    variant=product_['variant'],
                    stock=product_['stock'],
                    price=product_['price']
                )
            else:
                product = create_product(
                    name = product_['name'],
                    description=product_['description'],
                    categories=product_['categories'],
                    variant=product_['variant'],
                    stock=product_['stock'],
                    picture='',
                    price=product_['price']
                )
                sheets.products.set_id(name=product.name, id=product.id)
            if product.picture == '':
                update_required = True
                products_to_be_updated.append(product.id)
                

        if update_required:
            await state.update_data(products_to_be_updated=products_to_be_updated)
            await message.answer(f'{Lexicon.Admin.update_catalog__set_pictures} "{get_product(products_to_be_updated[0]).name}"')
            await state.set_state(FSMUpdateCatalog.set_pictures)
        else:
            await message.answer(Lexicon.Admin.update_catalog__success)
            
    except Exception as e:
        print(e)
        await message.answer(Lexicon.Admin.update_catalog__error)
    


@router.message(StateFilter(FSMUpdateCatalog.set_pictures), F.photo)
async def update_catalog_set_pictures(message: Message, state: FSMContext):
    products_to_be_updated = (await state.get_data())['products_to_be_updated']

    product_id = products_to_be_updated[0]
    picture = message.photo[-1].file_id
    product = update_product(product_id=product_id, picture=picture)

    products_to_be_updated=products_to_be_updated[1:]
    await state.update_data(products_to_be_updated=products_to_be_updated)

    if len(products_to_be_updated) > 0:
        await message.answer(
            f'{Lexicon.Admin.update_catalog__set_pictures} "{get_product(products_to_be_updated[0]).name}"'
        )
    else:
        await message.answer(Lexicon.Admin.update_catalog__success)
        await state.clear()
