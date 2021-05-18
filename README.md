# Momentum Stocks Screener in the Style of "Stocks on the Move" by Andreas Clenow
## How To Run
1. Open `config.yaml` and put in your preferences 
2. Run `momentum.py` **from the folder it is in**!
3. In the `output` folder you find
   - `momentum_positions.csv` - Your positions list
   - `Momentum.txt` - A TradingView watchlist



#### Separate Steps

Instead of running `momentum.py` you can also:

1. Run `momentum_data.py` to aggregate the price data
2. Run `momentum_posis.py` to aggregate your momentum positions list



#### Data Sources

##### Yahoo Finance

- Is default, no config necessary.

##### TD Ameritrade

1. Create TDAmeritrade Developer Account and App
2. Put in your `API_KEY` in `config.yaml`



## Calculation

### Momentum

Exponential regression is calculated like in this TradingView Indicator: https://www.tradingview.com/script/QWHjwm4B-Exponential-Regression-Slope-Annualized-with-R-squared-Histogram/
