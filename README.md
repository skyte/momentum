# Momentum Stocks Screener in the Style of "Stocks on the Move" by Andreas Clenow
## How To Run
1. Create TDAmeritrade Developer Account and App

2. Open "momentum_data.py" and put in

   - Your consumer key as API_KEY 

3. Run "momentum_data.py" to aggregate the price data

4. Open "momentum.py" and put in

   - ACCOUNT_VALUE

   - RISK_FACTOR

5. Run momentum.py to aggregate your momentum positions list

6. In the "output" folder you find

   - Your positions list
   - A TradingView watchlist



## Calculation

### Momentum

Exponential regression is calculated like in this TradingView Indicator: https://www.tradingview.com/script/QWHjwm4B-Exponential-Regression-Slope-Annualized-with-R-squared-Histogram/
