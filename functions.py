import requests
import json
import pandas as pd
import datetime


def test_get_history_dataframe():
    return pd.read_json("eurusd.json")


def test_get_live_dataframe():
    with open('live.json') as json_file:
        data = json.load(json_file)

    df = pd.json_normalize(data, "quotes")
    df["symbol"] = df["base_currency"] + df["quote_currency"]
    df.drop(["mid", "base_currency", "quote_currency"], axis=1, inplace=True)
    df = df[["symbol", "bid", "ask"]]
    return df


def get_live_dataframe():
    url = "https://marketdata.tradermade.com/api/v1/live?" \
          "currency=USDCAD,USDEUR,USDGBP,USDCHF,USDJPY&api_key=k1vu0zG0gE79rpya6SZO"

    response = requests.get(url)
    data = response.json()

    df = pd.json_normalize(data, "quotes")
    df["symbol"] = df["base_currency"] + df["quote_currency"]
    df.drop(["mid", "base_currency", "quote_currency"], axis=1, inplace=True)
    df = df[["symbol", "ask", "bid"]]

    return df


def get_history_dataframe(pair):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)

    url = f"https://marketdata.tradermade.com/api/v1/pandasDF?" \
          f"currency={pair}&" \
          f"api_key=k1vu0zG0gE79rpya6SZO&" \
          f"start_date={start_date}&" \
          f"end_date={end_date}&" \
          f"format=records&" \
          f"fields=ohlc"

    response = requests.get(url)
    data = response.json()
    df = pd.json_normalize(data)

    return df
