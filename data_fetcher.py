import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_spy_historical_data():
    # 创建一个 SPY ETF 的 ticker 对象
    spy = yf.Ticker("SPY")
    
    # 计算起始日期（30年前）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*30)
    
    # 下载历史数据
    df = spy.history(start=start_date, end=end_date)
    
    # 保存为 CSV 文件
    df.to_csv('spy_historical_data.csv')
    
    print(f"数据下载完成，共获取 {len(df)} 条记录")
    print(f"数据范围：从 {df.index[0].date()} 到 {df.index[-1].date()}")
    
    return df

if __name__ == "__main__":
    fetch_spy_historical_data()