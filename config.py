from dataclasses import dataclass
from environs import Env


@dataclass
class DatabaseConfig:
    url: str
    

@dataclass
class TgBot:
    token: str
    admin_ids: list[int]


@dataclass
class Lifepay:
    apikey: str
    login: str


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig
    lifepay: Lifepay
    sheet_key: str


def load_config() -> Config:

    path = '.env'
    env: Env = Env()
    env.read_env(path)

    db_user = env.str('POSTGRES_USER')
    db_password = env.str('POSTGRES_PASSWORD')
    db_name = env.str('POSTGRES_DB')

    lifepay_apikey = env.str('LIFEPAY_APIKEY')
    lifepay_login = env.str('LIFEPAY_LOGIN')

    return Config(
        tg_bot=TgBot(
            token=env.str('BOT_TOKEN'),
            admin_ids=[int(id) for id in env.list('ADMIN_IDS')]
        ),
        db=DatabaseConfig(
            url = f'postgresql+psycopg2://{db_user}:{db_password}@{db_name}:5432'
        ),
        lifepay=Lifepay(
            apikey=lifepay_apikey,
            login=lifepay_login
        ),
        sheet_key=env.str('SHEET_KEY'),
    )
