#%%
from loguru import logger
import yfinance as yf
import pandas as pd
import jquantsapi
import os
from datetime import date
import time

# logger.add("file_{time}.log")
#%%
# 銘柄コードの取得のためjquantsを使用
logger.info("銘柄リスト取得")
my_mail_address:str = os.environ['MAIL']
my_password: str = os.environ['JQUANTS_PW']
jq_cli = jquantsapi.Client(mail_address=my_mail_address, password=my_password)

stock_info_list = jq_cli.get_list()
stock_num = stock_info_list.shape[0]  

logger.info(f"Total number of stocks: {stock_num}")

if not os.path.exists("rawdata"):
    os.makedirs("rawdata")
dt_s = date(2010,1,1)
dt_e = date.today()

#%%

def save_stock_data(ticker_code: str, data_df: pd.DataFrame):
    """指定されたティッカーコードのデータをCSVファイルに保存する"""
    if data_df.empty:
        logger.warning(f"No data for {ticker_code}, skipping.")
        return
    
    # 不要な列を削除し、列名を整形
    # yfinanceは'Adj Close'を返すことがあるため、'Volume'までの6列に絞る
    # 存在する列のみを、指定した順序で抽出する
    cols_to_keep = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    existing_cols = [col for col in cols_to_keep if col in data_df.columns]
    df_to_save = data_df[existing_cols]
    
    # ファイルパスを生成して保存
    filepath = os.path.join("rawdata", f"{ticker_code}.csv")
    df_to_save.to_csv(filepath)
    logger.trace(f"Saved data for {ticker_code} to {filepath}")

#%%
# 全銘柄のティッカーリストを作成
tickers = [f"{code[:4]}.T" for code in stock_info_list['Code']]

# 動作テスト用
# tickers = tickers[:1]
# tickers

#%% レートリミット対策：ティッカーリストをチャンクに分割して処理
CHUNK_SIZE = 1000  # 1回のAPIコールで処理する銘柄数
WAIT_TIME_SEC = 60 # 各チャンク処理後の待機時間（秒）

def chunks(lst, n):
    """リストをサイズnのチャンクに分割するジェネレータ"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

ticker_chunks = list(chunks(tickers, CHUNK_SIZE))
total_chunks = len(ticker_chunks)

for i, ticker_chunk in enumerate(ticker_chunks):
    logger.info(f"Processing chunk {i+1}/{total_chunks} ({len(ticker_chunk)} tickers)...")
    
    # チャンクごとにデータをダウンロード
    chunk_data = yf.download(ticker_chunk, start=dt_s, end=dt_e, group_by='ticker', threads=True)
    
    # ダウンロードしたデータを銘柄ごとにファイルに保存
    for ticker in ticker_chunk:
        symbol = ticker.split('.')[0]
        stock_df = chunk_data.get(ticker)
        if stock_df is not None and not stock_df.empty:
            save_stock_data(symbol, stock_df)
        else:
            logger.warning(f"Could not retrieve data for {ticker}")
    
    if i < total_chunks - 1: # 最後のチャンク以外で待機
        logger.info(f"Waiting for {WAIT_TIME_SEC} seconds before next chunk...")
        time.sleep(WAIT_TIME_SEC)

logger.success("All chunks processed.")


# %%
