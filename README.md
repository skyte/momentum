# Momentum Stocks Screener in the Style of "Stocks on the Move" by Andreas Clenow
## How To Run

### Run EXE

1. Open the latest successful run here: https://github.com/skyte/momentum/actions
2. Download `exe-package` at the bottom (need to be logged in into github)
3. Exctract the `momentum` folder and enter it
   - If needed open `config.yaml` and put in your preferences 
4. Run `momentum.exe`



### Run Python Script

1. Open `config.yaml` and put in your preferences 
2. Install requirements: `python -m pip install -r requirements.txt`
3. Run `momentum.py`

#### Separate Steps

Instead of running `momentum.py` you can also:

1. Run `momentum_data.py` to aggregate the price data
2. Run `momentum_posis.py` to aggregate your momentum positions list



### \*\*\* Output \*\*\*

- in the `output` folder you will find:
  - your default (i.e. momentum calculated over the last 90 days) list of positions: `positions.csv`
  - your default TradingView watchlist: `Momentum.txt`
  - as well as the same thing for all other momentum calculations that you defined
    - in `config.yaml` add or remove values from `MOMENTUM_CALCULATION_PAST_DAYS`



## Config

#### Private File

You can create a `config_private.yaml` next to `config.yaml` and overwrite some parameters like `API_KEY`. That way you don't get conflicts when pulling a new version.

#### Data Sources

Can be switched with the field `DATA_SOURCE`

##### Yahoo Finance

(Benchmark: Loads 1500 Stocks in 20m)

- Is default, no config necessary.

##### TD Ameritrade

(Benchmark: Loads 1500 Stocks in 18m)

1. Create TDAmeritrade Developer Account and App
2. Put in your `API_KEY` in `config.yaml` and change `DATA_SOURCE`.



## Further Remarks

### Trading View Momentum Calculator

Here you can find a exponential regression TradingView indicator: https://www.tradingview.com/script/QWHjwm4B-Exponential-Regression-Slope-Annualized-with-R-squared-Histogram/  
Note that for some reason they calculate exp(slope) on the already exponential slope so the results will differ slightly.
