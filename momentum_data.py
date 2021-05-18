#!/usr/bin/env python
import requests
import json
import time
import bs4 as bs
import datetime as dt
import os
import pandas_datareader.data as web
import pickle
import requests
import yaml
import yfinance as yf
import pandas as pd

from datetime import date

if not os.path.exists('data'):
    os.makedirs('data')
if not os.path.exists('tmp'):
    os.makedirs('tmp')

try:
    with open(os.path.join('data','p_cfg.yaml'), 'r') as stream:
        p_cfg = yaml.safe_load(stream)
except FileNotFoundError:
    p_cfg = None
except yaml.YAMLError as exc:
        print(exc)

try:
    with open('config.yaml', 'r') as stream:
        cfg = yaml.safe_load(stream)
except FileNotFoundError:
    cfg = None
except yaml.YAMLError as exc:
        print(exc)
            
    
def getSecurities(url, tickerPos = 1, tablePos = 1, sectorPosOffset = 1, universe = "N/A"):
    resp = requests.get(url)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.findAll('table', {'class': 'wikitable sortable'})[tablePos-1]
    secs = {}
    for row in table.findAll('tr')[tablePos:]:
        sec = {}
        sec["ticker"] = row.findAll('td')[tickerPos-1].text.strip()
        sec["sector"] = row.findAll('td')[tickerPos-1+sectorPosOffset].text.strip()
        sec["universe"] = universe
        secs[sec["ticker"]] = sec
    with open(os.path.join("tmp", "tickers.pickle"), "wb") as f:
        pickle.dump(secs, f)
    return secs

def get_resolved_securities():
    tickers = {}
    if cfg["NQ100"]:
        tickers.update(getSecurities('https://en.wikipedia.org/wiki/Nasdaq-100', 2, 3, universe="Nasdaq 100"))
    if cfg["SP500"]:
        tickers.update(getSecurities('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies', sectorPosOffset=3, universe="S&P 500"))
    if cfg["SP400"]:
        tickers.update(getSecurities('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies', 2, universe="S&P 400"))
    if cfg["SP600"]:
        tickers.update(getSecurities('https://en.wikipedia.org/wiki/List_of_S%26P_600_companies', 2, universe="S&P 600"))
    return tickers

API_KEY = p_cfg["API_KEY"] if p_cfg else cfg["API_KEY"]
TD_API = cfg["TICKERS_API"]
TICKER_DATA_OUTPUT = os.path.join("data", "tickers_data.json")
SECURITIES = get_resolved_securities().values()
DATA_SOURCE = cfg["DATA_SOURCE"]

def construct_params(apikey=API_KEY, period_type="year", period=1, frequency_type="daily", frequency=1):
    """Returns tuple of api get params. Uses clenow default values."""

    return (
           ("apikey", apikey),
           ("periodType", period_type),
           ("period", period),
           ("frequencyType", frequency_type),
           ("frequency", frequency)
    ) 

def read_tickers(ticker_list=SECURITIES):
    """Reads list of tickers from a .txt file, expects one line per ticker"""
    with open(ticker_list, "r") as fp:
        return [ticker.strip() for ticker in fp.readlines()]

def process_ticker_json(ticker_response, security):
    ticker_response["sector"] = security["sector"]

def create_tickers_data_file(tickers_dict):
    with open(TICKER_DATA_OUTPUT, "w") as fp:
        json.dump(tickers_dict, fp)

def save_from_tda(securities):
    headers = {"Cache-Control" : "no-cache"}
    params = construct_params()
    tickers_dict = {}

    for idx, sec in enumerate(securities):
        response = requests.get(
                TD_API % sec["ticker"],
                params=params,
                headers=headers
        )
        # rate limit for td is 120 req/min
        time.sleep(0.5)
        ticker_data = response.json()
        process_ticker_json(ticker_data, sec)
        tickers_dict[sec["ticker"]] = ticker_data
        print(f'{sec["universe"]}: {sec["ticker"]} {response.status_code}')
    
    create_tickers_data_file(tickers_dict)


def get_yf_data(security, start_date, end_date):
        print(f'{security["universe"]}: {security["ticker"]}')
        df = yf.download(security["ticker"], start=start_date, end=end_date)
        yahoo_response = df.to_dict()
        timestamps = list(yahoo_response["Open"].keys())
        timestamps = list(map(lambda timestamp: int(timestamp.timestamp()), timestamps))
        opens = list(yahoo_response["Open"].values())
        closes = list(yahoo_response["Close"].values())
        lows = list(yahoo_response["Low"].values())
        highs = list(yahoo_response["High"].values())
        volumes = list(yahoo_response["Volume"].values())
        ticker_data = {}
        candles = []

        for i in range(0, len(opens)):
            candle = {}
            candle["open"] = opens[i]
            candle["close"] = closes[i]
            candle["low"] = lows[i]
            candle["high"] = highs[i]
            candle["volume"] = volumes[i]
            candle["datetime"] = timestamps[i]
            candles.append(candle)

        ticker_data["candles"] = candles
        process_ticker_json(ticker_data, security)
        return ticker_data

def save_from_yahoo(securities):
    today = date.today()
    start_date = today - dt.timedelta(days=1*365)
    tickers_dict = {}
    for sec in securities:
        ticker_data = get_yf_data(sec, start_date, today)
        tickers_dict[sec["ticker"]] = ticker_data
    create_tickers_data_file(tickers_dict)

def save_data(source, securities):
    if source == "YAHOO":
        save_from_yahoo(securities)
    elif source == "TD_AMERITRADE":
        save_from_tda(securities)
    

def main():
    save_data(DATA_SOURCE, SECURITIES)
    

if __name__ == "__main__":
    main()
