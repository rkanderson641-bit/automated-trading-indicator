# Automated Trading Indicator

Simple technical indicators for trading research.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Run the SMA crossover indicator against live price data:

```bash
python3 main.py AAPL --period 6mo --fast 10 --slow 30
```

This fetches daily closing prices for the ticker, computes a fast and slow
simple moving average, and prints BUY/SELL signals wherever the fast SMA
crosses the slow SMA.

### Library usage

```python
from sma import calculate_sma

prices = [10, 11, 12, 13, 14, 15]
calculate_sma(prices, window=3)
# [11.0, 12.0, 13.0, 14.0]
```
