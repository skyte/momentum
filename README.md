# Momentum Stocks Screener in the Style of "Stocks on the Move" by Andreas Clenow
## How To Run
1. Create TDAmeritrade Developer Account and App
2. Open `config.yaml` and put in your preferences
   - Don't forget to put in your `API_KEY`! 
3. Run `momentum.py`
4. In the `output` folder you find
   - `momentum_positions.csv` - Your positions list
   - `Momentum.txt` - A TradingView watchlist



#### Separate Steps

Instead of running `momentum.py` you can also:

1. Run `momentum_data.py` to aggregate the price data
2. Run `momentum_posis.py` to aggregate your momentum positions list



## Calculation

### Momentum

Exponential regression is calculated like in this TradingView Indicator: https://www.tradingview.com/script/QWHjwm4B-Exponential-Regression-Slope-Annualized-with-R-squared-Histogram/
