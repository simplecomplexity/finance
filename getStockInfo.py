import numpy as np
import pandas as pd
import yfinance as yf

"""
東京証券取引所の証券コード、社名一覧はGoogleで「上場会社一覧　日本取引所グループ JPX」と検索し、
検索結果の中から日本取引所グループ　東証上場銘柄一覧　のxlsファイルを取得する
"""

"""
PER: 株価収益率　株価が1株あたりの当期純利益(EPS)に対してどのくらい買われているか
EPS: 1株あたりの純利益　企業の収益力を示す指標
PBR: 株価純資産倍率　株価が1株あたりの純資産(BPS)に対してどのくらい買われているか
BPS: 1株あたりの純資産　企業の資産力を示す指標

PER = 株価/EPS
PBR = 株価/BPS
"""

def get_tse_dividend_info(ticker_code: str):
    """
    引数のticker_codeは証券コード（例: '7203'など）を想定。
    TSE上場銘柄の配当金データをDataFrameで返す。
    取得できない場合は空のDataFrameやエラーとなる可能性あり。
    """
    # yfinanceでは、TSE銘柄の場合「<証券コード>.T」をティッカーとして指定
    yf_ticker = f"{ticker_code}.T"

    # Tickerオブジェクトを作成
    ticker = yf.Ticker(yf_ticker)

    # dividends属性で配当履歴を取得 (pandas Series形式)
    dividends_series = ticker.dividends
    
    # Series -> DataFrameに変換し、列名を付けてみる
    df_dividends = dividends_series.to_frame(name="Dividend")
    df_dividends.reset_index(inplace=True)  # 日付を列にする
    df_dividends.rename(columns={"Date": "PayDate"}, inplace=True)
    
    return df_dividends

def get_tse_stock_price(ticker_code: str):
    """
    東京証券取引所(TSE)上場銘柄の現在(または直近)株価を取得する関数。
    引数のticker_codeは例: "7203" (トヨタ) のような数字のみを想定。
    yfinanceでは、TSE銘柄は "<コード>.T" と指定する。
    
    返り値:
      最新の終値 (float) を返す。
      取得できない場合は None を返す。
    """
    # yfinance用に「<コード>.T」という形式を作る
    yf_ticker = f"{ticker_code}.T"

    # yfinance で Tickerオブジェクトを生成
    ticker = yf.Ticker(yf_ticker)

    # 履歴情報 (ヒストリカルデータ) を取得
    # period='1d' は「直近1日分」のデータを要求
    # interval='1d' は日足
    data = ticker.history(period='1d', interval='1d')
    
    if data.empty:
        return None
    
    # 最終行の "Close" カラムを取得
    latest_close = data["Close"].iloc[-1]
    return latest_close

def get_tse_stock_eps(ticker_code: str):
    """
    東京証券取引所(TSE)銘柄のEPSを yfinance で取得を試みる関数。
    引数の ticker_code には、例: '7203' などの数字を指定。
    実際には yfinance では '7203.T' のように .T を付ける必要がある。

    取得可能なら float を返す。取得できなければ None を返す。
    """
    # yfinance用に「<コード>.T」という形式を作る
    yf_ticker = f"{ticker_code}.T"

    # yfinance で Tickerオブジェクトを生成
    ticker = yf.Ticker(yf_ticker)
    
    # yfinanceでは ticker.info['trailingEps'] や 'trailingEps' というキーで
    # EPSが取得できる場合がある。ただし必ずしも存在するとは限らない。
    info_dict = ticker.info  # dict
    
    # いくつかのキーが存在するケース: 'trailingEps', 'epsTrailingTwelveMonths', など
    possible_keys = ['trailingEps', 'epsTrailingTwelveMonths', 'forwardEps']
    eps_value = None
    
    for key in possible_keys:
        if key in info_dict:
            eps_value = info_dict[key]
            if eps_value is not None:
                break  # 最初に見つかったキーを使う

    return eps_value

def get_tse_stock_bps(ticker_code: str):
    """
    東京証券取引所(TSE)上場の銘柄について、BPS(1株あたり純資産)を
    yfinanceから取得する試みを行う関数。
    
    引数:
        ticker_code (str): 例 "7203" のような証券コード
    
    返り値:
        float | None: 取得したBPS。取得できなければ None。
    """
    # yfinance で日本株は "<コード>.T" と表記
    yf_ticker = f"{ticker_code}.T"

    # yfinance で Tickerオブジェクトを生成
    ticker = yf.Ticker(yf_ticker)

    # dict形式で銘柄情報を取得
    info_dict = ticker.info
    
    # yfinance上でBPSに相当するキーは "bookValue" や "bookValuePerShare" などがある場合がある
    # ただし存在しないことも多い
    possible_keys = ["bookValue", "bookValuePerShare"]
    
    bps_value = None
    for key in possible_keys:
        if key in info_dict:
            bps_value = info_dict[key]
            if bps_value is not None:
                break  # 最初に見つかった値を使用
    
    return bps_value

def get_ticker(ticker):
    print(ticker)
    # 履歴情報 (ヒストリカルデータ) を取得
    # period='1d' は「直近1日分」のデータを要求
    # interval='1d' は日足
    data = ticker.history(period='1d', interval='1d')
    
    if data.empty:
        return None
    
    # 最終行の "Close" カラムを取得
    latest_close = data["Close"].iloc[-1]
    return latest_close

def selecter(ticker_code:str, dividend:bool, stock_price:bool, eps:bool, bps:bool ):
    #print('ticker = ' + ticker_code)
    # yfinance で日本株は "<コード>.T" と表記
    yf_ticker = f'{ticker_code}.T'
    # yfinance で Tickerオブジェクトを生成
    ticker = yf.Ticker(yf_ticker)
    print(type(ticker))
    str = get_ticker(ticker)
    return str

def main():
    # 例: トヨタ自動車(証券コード7203)の配当金データを取得
    # 例: ソニーグループ(証券コード6758)
    codes = ['7203', '6758', '5016']

    flg_dividend = False
    flg_stock_price = False
    flg_eps = False
    flg_bps = False

    ## 配当履歴
    if flg_dividend == True:
        for i in range(len(codes)):
            dividend_df = get_tse_dividend_info(codes[i])

            if not dividend_df.empty:
                print(f' [{codes[i]} の配当履歴]')
                print(dividend_df)
            else:
                print(f'¥n 配当データが取得できませんでした: {codes[i]}')
    
    ## 株価
    if flg_stock_price == True:
        for i in range(len(codes)):
            price = get_tse_stock_price(codes[i])

            if price is not None:
                print(f'証券コード{codes[i]}の直近株価: {price:.2f}')
            else:
                print(f'株価を取得できませんでした (code={codes[i]})')

    ## EPS 一株あたりの純利益
    if flg_eps == True:
        for i in range(len(codes)):
            eps = get_tse_stock_eps(codes[i])

            if eps is not None:
                print(f'証券コード {codes[i]} のEPS: {eps}')
            else:
                print(f'証券コード {codes[i]} のEPSが取得できませんでした。')

    ## BPS 一株あたりの純資産
    if flg_bps == True:
        for i in range(len(codes)):
            bps = get_tse_stock_bps(codes[i])

            if bps is not None:
                print(f'証券コード {codes[i]} のBPS: {bps}')
            else:
                print(f'証券コード {codes[i]} のBPSが取得できませんでした。')

    print(selecter(codes[0], flg_dividend, flg_stock_price, flg_eps, flg_bps))

if __name__ == "__main__":
    main()