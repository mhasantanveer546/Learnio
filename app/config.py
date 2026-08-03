import os
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "unsafe-secret"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///"
        + os.path.join(
            BASE_DIR,
            "..",
            "instance",
            "learnio.db"
        )
    )


class ProductionConfig(Config):

    DEBUG = False

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    )


config = {

    "development": DevelopmentConfig,

    "production": ProductionConfig

}