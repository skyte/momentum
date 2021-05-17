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
import json


from datetime import date

if not os.path.exists('data'):
    os.makedirs('data')

try:
    with open(os.path.join('data','cfg.json')) as f:
      cfg = json.load(f)
except FileNotFoundError:
    cfg = None

def save_tickers(url, tickerPos = 1, tablePos = 1):
    resp = requests.get(url)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.findAll('table', {'class': 'wikitable sortable'})[tablePos-1]
    tickers = []
    for row in table.findAll('tr')[tablePos:]:
        ticker = row.findAll('td')[tickerPos-1].text
        tickers.append(ticker.strip())
    with open(os.path.join("tmp", "tickers.pickle"), "wb") as f:
        pickle.dump(tickers, f)
    return tickers

def save_sp400_tickers():
    return save_tickers('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies', 2)

def save_sp500_tickers():
    return save_tickers('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')

def save_sp600_tickers():
    return save_tickers('https://en.wikipedia.org/wiki/List_of_S%26P_600_companies', 2)

def save_nesquik_tickers():
    return save_tickers('https://en.wikipedia.org/wiki/Nasdaq-100', 2, 3)


API_KEY = cfg["apiKey"] if cfg else "Your_API_Key"
TD_API = "https://api.tdameritrade.com/v1/marketdata/%s/pricehistory"
# TICKER_DATA_OUTPUT = "sp500-nasdaq-daily-{}.json".format(date.today())
TICKER_DATA_OUTPUT = os.path.join("data", "tickers_data.json")
TICKERS = save_sp500_tickers()
# TICKERS = save_nesquik_tickers()


def construct_params(apikey=API_KEY, period_type="year", period=1, frequency_type="daily", frequency=1):
    """Returns tuple of api get params. Uses clenow default values."""

    return (
           ("apikey", apikey),
           ("periodType", period_type),
           ("period", period),
           ("frequencyType", frequency_type),
           ("frequency", frequency)
    ) 
    

def read_tickers(ticker_list=TICKERS):
    """Reads list of tickers from a .txt file, expects one line per ticker"""
    with open(ticker_list, "r") as fp:
        return [ticker.strip() for ticker in fp.readlines()]



def process_ticker_json(ticker_dict, ticker_response):
    """Processes ticker json data into global ticker dict""" 
    symbol = ticker_response["symbol"]
    ticker_dict[symbol] = ticker_response

        

def main():
    headers = {"Cache-Control" : "no-cache"}
    tickers = TICKERS
    params = construct_params()
    ticker_dict = {}

    for idx, ticker in enumerate(tickers):
        response = requests.get(
                TD_API % ticker,
                params=params,
                headers=headers
        )
        # rate limit for td is 120 req/min
        time.sleep(0.5)
        process_ticker_json(ticker_dict, response.json())
        print(ticker, response.status_code)
    
    with open(TICKER_DATA_OUTPUT, "w") as fp:
        json.dump(ticker_dict, fp)

if __name__ == "__main__":
    main()
