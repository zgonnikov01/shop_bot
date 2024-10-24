import asyncio, sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from environs import Env


import handlers.admin.basic
import handlers.admin.add_products
import handlers.admin.edit_products

import handlers.user.basic
import handlers.user.sign_up

from db.methods import create_db_and_tables

from config import load_config


create_db_and_tables()

config = load_config()

#env: Env = Env()
#env.read_env('.env')

#bot_token = env.str('BOT_TOKEN')
#bot_token = env.str('TEST_TOKEN')

bot_token = config.tg_bot.token


redis = Redis(host='redis', port=6379)
storage = RedisStorage(redis=redis)


bot = Bot(bot_token)

dp = Dispatcher(storage=storage)

dp.include_routers(
    handlers.admin.basic.router,
    handlers.admin.add_products.router,
    handlers.admin.edit_products.router,

    handlers.user.basic.router,
    handlers.user.sign_up.router
)



async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
