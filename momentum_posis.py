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
RISK_FACTOR = cfg("RISK_FACTOR")
MAX_STOCKS = cfg("STOCKS_COUNT_OUTPUT")
SLOPE_DAYS = cfg("MOMENTUM_CALCULATION_PAST_DAYS")
POS_COUNT_TARGET = cfg("POSITIONS_COUNT_TARGET")

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
    return (((np.exp(slope) ** 253) - 1) * 100) * (r**2)

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
    """Returns a dataframe doubly sorted by deciles and momentum factor, with atr and position size"""
    json = read_json(PRICE_DATA)
    momentums = {}
    ranks = []
    for ticker in json:
        closes = []
        try:
            for candle in json[ticker]["candles"]:
                closes.append(candle["close"])
            if closes:
                diffs = np.abs(pd.Series(closes).pct_change().diff()).dropna()
                gaps = diffs[diffs > 0.15]
                ma = pd.Series(closes).rolling(100).mean().tail(1).item()
                if ma > closes[-1]:
                    print("%s is below it's 100d moving average." % ticker)
                elif len(gaps):
                    print("%s has a gap > 15%%" % ticker)
                else:
                    ranks.append(len(ranks)+1)
                    for slope_days in SLOPE_DAYS:
                        if not slope_days in momentums:
                            momentums[slope_days] = []
                        mmntm = momentum(pd.Series(closes).tail(slope_days))
                        momentums[slope_days].append((0, ticker, json[ticker]["sector"], mmntm, atr_20(json[ticker]["candles"]), closes[-1]))
        except KeyError:
            print(f'Ticker {ticker} has corrupted data.')
    title_rank = "Rank"
    title_ticker = "Ticker"
    title_sector = "Sector"
    title_momentum = "Momentum (%)"
    title_risk = "ATR20d"
    title_price = "Price"
    title_amount = "Shares"
    title_pos_size = "Position ($)"
    title_sum = "Sum ($)"
    slope_std = SLOPE_DAYS[0]
    dfs = []
    for slope_days in SLOPE_DAYS:
        slope_suffix = f'_{slope_days}' if slope_days != slope_std else ''
        df = pd.DataFrame(momentums[slope_days], columns=[title_rank, title_ticker, title_sector, title_momentum, title_risk, title_price])
        df = df.sort_values(([title_momentum]), ascending=False)
        df[title_rank] = ranks
        # df["decile"] = pd.qcut(df["momentum %"], 10, labels=False)
        df[title_amount] = calc_stocks_amount(ACCOUNT_VALUE, RISK_FACTOR, df[title_risk])
        df[title_pos_size] = calc_pos_size(df[title_amount], df[title_price])
        (sums, stocks_count) = calc_sums(ACCOUNT_VALUE, df[title_pos_size])
        df[title_sum] = sums
        # recalculate for stocks target
        if POS_COUNT_TARGET and (stocks_count < POS_COUNT_TARGET or stocks_count - POS_COUNT_TARGET > 5):
            adjusted_risk_factor = RISK_FACTOR * (stocks_count / POS_COUNT_TARGET)
            df[title_amount] = calc_stocks_amount(ACCOUNT_VALUE, adjusted_risk_factor, df[title_risk])
            df[title_pos_size] = calc_pos_size(df[title_amount], df[title_price])
            (sums, stocks_count) = calc_sums(ACCOUNT_VALUE, df[title_pos_size])
            df[title_sum] = sums

        df.head(MAX_STOCKS).to_csv(os.path.join(DIR, "output", f'positions{slope_suffix}.csv'), index = False)

        watchlist = open(os.path.join(DIR, "output", f'Momentum{slope_suffix}.txt'), "w")
        watchlist.write(','.join(df.head(MAX_STOCKS)[title_ticker]))
        watchlist.close()

        dfs.append(df)

    return dfs


def main():
    posis = positions()
    print(posis[0])

if __name__ == "__main__":
    main()
