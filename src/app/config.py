import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = os.environ['DEBUG'] == 'True'
    ENV = os.environ['ENV']

    APP_NAME = 'deribit-price-tracker'
    BASE_DIR = basedir

    HOST = os.environ['HOST']
    PORT = int(os.environ['PORT'])

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s | testos | %(levelname)s | %(name)s | %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
        },
        'loggers': {
            APP_NAME: {'level': 'DEBUG' if DEBUG else 'ERROR', 'handlers': ['console']},
            'sqlalchemy.engine': {'level': 'ERROR', 'handlers': ['console']},
        },
    }

    # Настройки базы данных.
    # 'postgresql://username:password@host:port/db_name'
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://'
        f'{os.environ["POSTGRES_USER"]}:{os.environ["POSTGRES_PASSWORD"]}'
        f'@{os.environ["POSTGRES_HOST"]}:{os.environ["POSTGRES_PORT"]}'
        f'/{os.environ["POSTGRES_DB"]}'
    )
    if ENV == 'production':
        SQLALCHEMY_ENGINE_OPTIONS = {
            'connect_args': {'target_session_attrs': 'read-write', 'sslmode': 'verify-full'}
        }
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pagination.
    ITEMS_PER_PAGE = os.environ.get('ITEMS_PER_PAGE') or 20
    MAX_PER_PAGE = os.environ.get('MAX_PER_PAGE') or 100
