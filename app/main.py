from fastapi import FastAPI, HTTPException
from analytics.queries import get_price_trend, compare_markets, get_volatility
from datetime import datetime

app = FastAPI()

@app.get('/volatility')
async def get_data_for_volatility(commodity, market, start_date=None, end_date=None):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    try:
        result = get_volatility(commodity, market, start_date, end_date)
        if result is None or result ==[]:
            raise HTTPException(
                status_code=404,
                detail="No data found for the given commodity and date interval."
            )
        return {"volatility":result}
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=505,
            detail="An error occured while processing the request")

@app.get('/compare-market')
async def get_data_for_market_comparision(commodity, start_date=None, end_date=None):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    try:
        result = compare_markets(commodity, start_date, end_date)
        if result is None or result ==[]:
            raise HTTPException(
                status_code=404,
                detail="No data found for the given commodity and date interval."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An error occured while processing the request."
        )

@app.get("/price-trend")
async def get_data_for_price_trend(commodity, market, start_date=None, end_date=None):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    try:
        result = get_price_trend(commodity, market, start_date=None, end_date=None)
        if result is None or result ==[]:
            raise HTTPException(
                status_code=404,
                detail="No data found for the given commodity and date interval."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An error occured while processing the request."
        )



