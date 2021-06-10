import sys
import pandas as pd
import numpy as np
import json
import os
from datetime import date
from scipy.stats import linregress
import yaml
from momentum_data import cfg

DIR = os.path.dirname(os.path.realpath(__file__))

pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

try:
    with open('config.yaml', 'r') as stream:
        config = yaml.safe_load(stream)
except FileNotFoundError:
    config = None
except yaml.YAMLError as exc:
        print(exc)

PRICE_DATA = os.path.join(DIR, "data", "price_history.json")
ACCOUNT_VALUE = cfg("CASH")
RISK_FACTOR_CFG = cfg("RISK_FACTOR")
RISK_FACTOR = RISK_FACTOR_CFG or 0.002
MAX_STOCKS = cfg("STOCKS_COUNT_OUTPUT")
SLOPE_DAYS = cfg("MOMENTUM_CALCULATION_PAST_DAYS")
POS_COUNT_TARGET = cfg("POSITIONS_COUNT_TARGET")
MAX_GAP = cfg("EXCLUDE_MAX_GAP_PCT")
EXCLUDE_MA_CROSSES = cfg("EXCLUDE_ALL_MA_CROSSES")

TITLE_RANK = "Rank"
TITLE_TICKER = "Ticker"
TITLE_SECTOR = "Sector"
TITLE_UNIVERSE = "Universe"
TITLE_PERCENTILE = "Percentile"
TITLE_MOMENTUM = "Momentum (%)"
TITLE_RISK = "ATR20d"
TITLE_PRICE = "Price"
TITLE_SHARES = "Shares"
TITLE_POS_SIZE = "Position ($)"
TITLE_SUM = "Sum ($)"

if not os.path.exists('output'):
    os.makedirs('output')

def read_json(json_file):
    with open(json_file, "r") as fp:
        return json.load(fp)

def momentum(closes):
    """Calculates slope of exp. regression normalized by rsquared"""
    returns = np.log(closes)
    indices = np.arange(len(returns))
    slope, _, r, _, _ = linregress(indices, returns)
    # return ((1 + slope) ** 253) * (r**2)
    return (((np.exp(slope) ** 252) - 1) * 100) * (r**2)

def atr_20(candles):
    """Calculates last 20d ATR"""
    daily_atrs = []
    for idx, candle in enumerate(candles):
        high = candle["high"]
        low = candle["low"]
        prev_close = 0
        if idx > 0:
            prev_close = candles[idx - 1]["close"]
        daily_atr = max(high-low, np.abs(high - prev_close), np.abs(low - prev_close))
        daily_atrs.append(daily_atr)
    return pd.Series(daily_atrs).rolling(20).mean().tail(1).item()

def calc_stocks_amount(account_value, risk_factor, risk_input):
    return (np.floor(account_value * risk_factor / risk_input)).astype(int)

def calc_pos_size(amount, price):
    return np.round(amount * price, 2)

def calc_sums(account_value, pos_size):
    sums = []
    sum = 0
    stocks_count = 0
    for position in list(pos_size):
            sum = sum + position
            sums.append(sum)
            if sum < account_value:
                stocks_count = stocks_count + 1
    return (sums, stocks_count)

def positions():
    """Returns a dataframe doubly sorted by momentum factor, with atr and position size"""
    json = read_json(PRICE_DATA)
    momentums = {}
    ranks = []
    for ticker in json:
        try:
            closes = list(map(lambda candle: candle["close"], json[ticker]["candles"]))
            if closes:
                closes_series = pd.Series(closes)
                slope_series = closes_series.tail(SLOPE_DAYS[0])
                mas = closes_series.rolling(100).mean().tail(SLOPE_DAYS[0])
                ma_is_crossed = False
                if (EXCLUDE_MA_CROSSES):
                    ma_crosses = slope_series < mas
                    ma_crosses = ma_crosses.where(ma_crosses == True).dropna()
                    ma_is_crossed = ma_crosses.size > 0
                # calculate gaps of the last 90 days
                diffs = np.abs(slope_series.pct_change().diff()).dropna()
                gaps = diffs[diffs > MAX_GAP / 100.0]
                ma = mas.tail(1).item()
                if ma > closes[-1] or ma_is_crossed:
                    print("%s was below it's 100d moving average." % ticker)
                elif len(gaps):
                    print(f'{ticker} has a gap > {MAX_GAP}%')
                else:
                    ranks.append(len(ranks)+1)
                    for idx, slope_days in enumerate(SLOPE_DAYS):
                        if not slope_days in momentums:
                            momentums[slope_days] = []
                        mmntm = momentum(pd.Series(closes[-slope_days:]))
                        momentums[slope_days].append((0, ticker, json[ticker]["sector"], json[ticker]["universe"], mmntm, atr_20(json[ticker]["candles"]), closes[-1]))
        except KeyError:
            print(f'Ticker {ticker} has corrupted data.')
    slope_std = SLOPE_DAYS[0]
    dfs = []
    for slope_days in SLOPE_DAYS:
        slope_suffix = f'_{slope_days}' if slope_days != slope_std else ''
        df = pd.DataFrame(momentums[slope_days], columns=[TITLE_RANK, TITLE_TICKER, TITLE_SECTOR, TITLE_UNIVERSE, TITLE_MOMENTUM, TITLE_RISK, TITLE_PRICE])
        df = df.sort_values(([TITLE_MOMENTUM]), ascending=False)
        df[TITLE_RANK] = ranks
        # df[TITLE_PERCENTILE] = pd.qcut(df[TITLE_MOMENTUM], 100, labels=False)
        df = df.head(MAX_STOCKS)
        risk_factor = RISK_FACTOR
        calc_runs = 2
        for run in range(1,calc_runs+1,1):
            # recalculate for positions target
            if run > 1 and not RISK_FACTOR_CFG and POS_COUNT_TARGET and (stocks_count < POS_COUNT_TARGET or stocks_count - POS_COUNT_TARGET > 1):
                risk_factor = RISK_FACTOR * (stocks_count / POS_COUNT_TARGET)
            df[TITLE_SHARES] = calc_stocks_amount(ACCOUNT_VALUE, risk_factor, df[TITLE_RISK])
            df[TITLE_POS_SIZE] = calc_pos_size(df[TITLE_SHARES], df[TITLE_PRICE])
            (sums, stocks_count) = calc_sums(ACCOUNT_VALUE, df[TITLE_POS_SIZE])
            df[TITLE_SUM] = sums

        df.to_csv(os.path.join(DIR, "output", f'mmtm_posis{slope_suffix}.csv'), index = False)

        watchlist = open(os.path.join(DIR, "output", f'Momentum{slope_suffix}.txt'), "w")
        first_10_pf = ""
        tv_ticker_count = 0
        for index, row in df.iterrows():
            plus_sign = "" if tv_ticker_count == 0 else "+"
            # TradingView only supports combining 10 Tickers :(((
            if row[TITLE_POS_SIZE] > 0 and row[TITLE_SUM] <= ACCOUNT_VALUE and tv_ticker_count < 10:
                tv_ticker_count = tv_ticker_count + 1
                first_10_pf = f'{first_10_pf}{plus_sign}{row[TITLE_SHARES]}*{row[TITLE_TICKER]}'
        # first_10_combined = f'{first_10_combined})/{tv_ticker_count}'
        watchlist_stocks = ','.join(df.head(MAX_STOCKS)[TITLE_TICKER])
        watchlist.write(f'{first_10_pf},{watchlist_stocks}')
        watchlist.close()

        dfs.append(df)

    return dfs


def main():
    posis = positions()
    print(posis[0])
    print("***\nYour 'mmtm_posis.csv' is in the output folder.\n***")
    if cfg("EXIT_WAIT_FOR_ENTER"):
        input("Press Enter key to exit...")

if __name__ == "__main__":
    main()
