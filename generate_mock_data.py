import requests
import pandas as pd
import time
import os


def download_binance_klines(symbol='BTCUSDT', interval='1m', limit=1000):
    """
    从币安公开 API 获取历史K线
    interval: 1m, 5m, 15m, 1h, 4h, 1d 等
    limit: 单次最大 1000
    """
    os.makedirs('data', exist_ok=True)

    all_klines = []
    start_time = None
    # 最多获取 10000 条（可调整）
    for _ in range(10):  # 10次请求 * 1000 = 10000条
        url = 'https://api.binance.com/api/v3/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        if start_time:
            params['startTime'] = start_time

        resp = requests.get(url, params=params)
        data = resp.json()
        if not data:
            break

        all_klines.extend(data)
        # 更新起始时间为最后一条的时间+1ms
        start_time = data[-1][0] + 1
        time.sleep(0.1)  # 避免请求过快

    # 解析为 DataFrame
    df = pd.DataFrame(all_klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['price'] = df['close'].astype(float)
    df['bid'] = df['price'] * 0.9995
    df['ask'] = df['price'] * 1.0005
    df['symbol'] = symbol

    df = df[['timestamp', 'symbol', 'price', 'bid', 'ask', 'volume']]
    df.to_csv('data/BTCUSDT_binance.csv', index=False)
    print(f"成功下载 {len(df)} 条数据，保存至 data/BTCUSDT_binance.csv")


if __name__ == '__main__':
    download_binance_klines(interval='1m', limit=1000)