import logging

from app.database import SessionLocal
from app.services.price_service import PriceService
from celery import shared_task
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@shared_task
def fetch_prices_task():
    """Задача Celery для получения цен каждую минуту"""
    db: Session = SessionLocal()
    try:
        prices = PriceService.fetch_and_store_prices(db)
        logger.info(f'Полеченные цены {prices}')
        return prices
    except Exception as e:
        logger.error(f'Ошибка при получении цен: {str(e)}')
        raise
    finally:
        db.close()
