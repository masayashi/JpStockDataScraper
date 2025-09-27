#%%
from loguru import logger
import yfinance as yf
import pandas as pd
import jquantsapi
import os
from datetime import date
import time

#%%
df = yf.download("7203.T", period="1y")
df
# %%

# 複数の日本株ティッカーで試す
tickers = ["7203.T", "6758.T", "8031.T"]
data = yf.download(tickers, period="1d")
# %%
