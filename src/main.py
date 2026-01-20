import logging
import time
from contextlib import asynccontextmanager

from app.api.v1.endpoints import prices
from app.config import Config
from app.database import engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG else logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Ожидание базы данных')
    max_retries = 30
    retry_delay = 2

    for try_number in range(max_retries):
        try:
            with engine.connect() as conn:
                logger.info('База данных готова')
                break
        except Exception as e:
            if try_number < max_retries - 1:
                logger.warning(f'База не готова (попытка {try_number + 1}/{max_retries}): {e}')
                time.sleep(retry_delay)
            else:
                logger.error('Не удалось запустить базу данных')
                raise

    yield


app = FastAPI(title=Config.APP_NAME, version='1.0.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(prices.router, prefix='/api/v1')


@app.get('/')
async def root():
    return {
        'message': f'{Config.APP_NAME}',
        'version': '1.0.0',
        'endpoints': {
            'get_all_prices': '/api/v1/prices/',
            'get_latest_price': '/api/v1/prices/latest',
            'get_price_by_date': '/api/v1/prices/by-date',
        },
    }


@app.get('/health')
async def health_check():
    return {'status': 'healthy'}
