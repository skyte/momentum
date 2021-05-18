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

def getSecurities(url, tickerPos = 1, tablePos = 1, sectorPosOffset = 1):
    resp = requests.get(url)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.findAll('table', {'class': 'wikitable sortable'})[tablePos-1]
    secs = {}
    for row in table.findAll('tr')[tablePos:]:
        sec = {}
        sec["ticker"] = row.findAll('td')[tickerPos-1].text.strip()
        sec["sector"] = row.findAll('td')[tickerPos+sectorPosOffset-1].text
        secs[sec["ticker"]] = sec
    with open(os.path.join("tmp", "tickers.pickle"), "wb") as f:
        pickle.dump(secs, f)
    return secs

def get_resolved_securities():
    tickers = {}
    if cfg["NQ100"]:
        tickers.update(getSecurities('https://en.wikipedia.org/wiki/Nasdaq-100', 2, 3))
    if cfg["SP500"]:
        tickers.update(getSecurities('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies', sectorPosOffset=2))
    if cfg["SP400"]:
        tickers.update(getSecurities('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies', 2))
    if cfg["SP600"]:
        tickers.update(getSecurities('https://en.wikipedia.org/wiki/List_of_S%26P_600_companies', 2))
    return tickers

API_KEY = p_cfg["API_KEY"] if p_cfg else cfg["API_KEY"]
TD_API = cfg["TICKERS_API"]
TICKER_DATA_OUTPUT = os.path.join("data", "tickers_data.json")
SECURITIES = get_resolved_securities().values()

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

def process_ticker_json(ticker_dict, ticker_response, security):
    """Processes ticker json data into global ticker dict""" 
    symbol = security["ticker"]
    ticker_response["sector"] = security["sector"]
    ticker_dict[symbol] = ticker_response 

def main():
    headers = {"Cache-Control" : "no-cache"}
    secs = SECURITIES
    params = construct_params()
    ticker_dict = {}

    for idx, sec in enumerate(secs):
        response = requests.get(
                TD_API % sec["ticker"],
                params=params,
                headers=headers
        )
        # rate limit for td is 120 req/min
        time.sleep(0.5)
        process_ticker_json(ticker_dict, response.json(), sec)
        print(sec["ticker"], response.status_code)
    
    with open(TICKER_DATA_OUTPUT, "w") as fp:
        json.dump(ticker_dict, fp)

if __name__ == "__main__":
    main()
