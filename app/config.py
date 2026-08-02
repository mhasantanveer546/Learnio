import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "development-secret-key"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///learnio.db"
    )


class ProductionConfig(Config):

    DEBUG = False

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    )


config = {

    "development": DevelopmentConfig,

    "production": ProductionConfig,

}