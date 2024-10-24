from aiogram import Bot
from aiogram.types import BotCommand
from aiogram.types.bot_command_scope_chat import BotCommandScopeChat
from lexicon.lexicon_ru import Lexicon


async def set_user_menu(chat_id: int, bot: Bot):
    items = [BotCommand(command=item[0], description=item[1]) for item in Lexicon.User.menu.items()]
    await bot.set_my_commands(commands=items, scope=BotCommandScopeChat(chat_id=chat_id))


async def set_admin_menu(chat_id: int, bot: Bot):
    items = [
        BotCommand(
            command=item[0],
            description=item[1]
        ) for item in Lexicon.Admin.menu.items() | Lexicon.User.menu.items()
    ]
    await bot.set_my_commands(items, scope=BotCommandScopeChat(chat_id=chat_id))
