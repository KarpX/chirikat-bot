from dataclasses import dataclass
import os
from dotenv import load_dotenv

@dataclass
class BotConfig:
    token: str

@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    db: str

@dataclass
class Config:
    bot: BotConfig
    database: DatabaseConfig

def load_config() -> Config:
    load_dotenv()

    bot_config = BotConfig(token=os.getenv("BOT_TOKEN"))
    database_config = DatabaseConfig(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME")
    )

    return Config(bot=bot_config, database=database_config)