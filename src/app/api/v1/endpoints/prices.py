from datetime import datetime

from app.database import get_db
from app.services.price_service import PriceService
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix='/prices', tags=['prices'])


class PriceResponse(BaseModel):
    id: int
    ticker: str
    price: float
    timestamp: int
    created_at: datetime | None

    class Config:
        from_attributes = True


@router.get('/', response_model=list[PriceResponse])
def get_all_prices(
    ticker: str = Query(..., description='Ticker'),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    if ticker.upper() not in ['BTC_USD', 'ETH_USD']:
        raise HTTPException(status_code=400, detail='Неверный ticker')

    prices = PriceService.get_all_prices(db, ticker.upper(), skip, limit)
    return prices


@router.get('/latest', response_model=PriceResponse)
def get_latest_price(
    ticker: str = Query(..., description='Ticker'),
    db: Session = Depends(get_db)
):
    if ticker.upper() not in ['BTC_USD', 'ETH_USD']:
        raise HTTPException(status_code=400, detail='Неверный ticker')

    price = PriceService.get_latest_price(db, ticker.upper())
    if not price:
        raise HTTPException(status_code=404, detail='Цены не найдены')
    return price


@router.get('/by-date', response_model=list[PriceResponse])
def get_price_by_date(
    ticker: str = Query(..., description='Ticker'),
    date_from: datetime | None = Query(None, description='Дата начала'),
    date_to: datetime | None = Query(None, description='Дата конца'),
    db: Session = Depends(get_db),
):
    if ticker.upper() not in ['BTC_USD', 'ETH_USD']:
        raise HTTPException(status_code=400, detail='Неверный ticker')

    prices = PriceService.get_price_by_date(db, ticker.upper(), date_from, date_to)
    return prices
