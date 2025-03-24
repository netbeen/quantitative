import pandas as pd
import numpy as np
import mplfinance as mpf
from data_fetcher import fetch_spy_historical_data
from datetime import datetime, timedelta

def calculate_investment_amount(current_price, ma20):
    """计算每次投资金额"""
    drop_percentage = (ma20 - current_price) / ma20 * 100
    
    if drop_percentage <= 0:  # 盈利
        return 500
    elif 0 < drop_percentage <= 5:
        return 1000
    elif 5 < drop_percentage <= 10:
        return 1500
    elif 10 < drop_percentage <= 15:
        return 2000
    elif 15 < drop_percentage <= 20:
        return 2500
    else:  # > 20%
        return 3000

def plot_backtest_results(df, investments):
    # 将投资记录转换为适合绘图的格式
    buy_dates = [pd.Timestamp(inv['date']) for inv in investments]
    buy_prices = [inv['price'] for inv in investments]
    buy_amounts = [inv['investment'] for inv in investments]
    
    # 计算每个时间点的持仓成本
    cost_basis = []
    running_total_cost = 0
    running_total_shares = 0
    
    for date in df.index:
        matching_inv = [inv for inv in investments if pd.Timestamp(inv['date']) <= date]
        if matching_inv:
            running_total_cost = matching_inv[-1]['total_invested']
            running_total_shares = matching_inv[-1]['total_shares']
            cost_basis.append(running_total_cost / running_total_shares if running_total_shares > 0 else np.nan)
        else:
            cost_basis.append(np.nan)
    
    df['Cost_Basis'] = cost_basis
    
    # 准备绘图数据
    df_plot = df.copy()
    
    # 设置绘图样式
    mc = mpf.make_marketcolors(up='red', down='green', edge='inherit',
                              wick='inherit', volume='inherit')
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle='dotted')
    
    # 添加均线和成本线
    addplot = [
        mpf.make_addplot(df['MA20'], color='orange', width=1, label='MA20'),
        mpf.make_addplot(df['Cost_Basis'], color='purple', width=1, label='持仓成本')
    ]
    
    # 绘制图表
    fig, axes = mpf.plot(
        df_plot,
        type='candle',
        style=s,
        title='SPY 投资策略回测结果',
        volume=True,
        addplot=addplot,
        returnfig=True,
        figsize=(15, 10)
    )
    
    # 手动添加买入点标记
    for date, price, amount in zip(buy_dates, buy_prices, buy_amounts):
        axes[0].scatter(df_plot.index.get_loc(date), price, 
                       marker='^', color='blue', s=100)
        axes[0].annotate(f'${amount}', 
                        (df_plot.index.get_loc(date), price),
                        xytext=(5, 5), textcoords='offset points')
    
    # 添加图例
    axes[0].legend(['MA20', '持仓成本'])
    
    # 保存图表
    import matplotlib.pyplot as plt
    plt.savefig('backtest_visualization.png', bbox_inches='tight', dpi=300)
    plt.close()

def backtest_strategy():
    # 获取历史数据
    df = fetch_spy_historical_data()
    
    # 计算20日移动平均线
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # 设置回测起始时间（10年前），并转换为纽约时区
    start_date = pd.Timestamp.now(tz='America/New_York') - pd.DateOffset(years=10)
    df = df[df.index >= start_date]
    
    # 初始化投资记录
    investments = []
    total_invested = 0
    total_shares = 0
    
    # 遍历每个交易日
    for date, row in df.iterrows():
        # 检查是否是每月9号
        if date.day == 9:
            if not np.isnan(row['MA20']):  # 确保MA20有值
                investment_amount = calculate_investment_amount(row['Close'], row['MA20'])
                shares_bought = investment_amount / row['Close']
                
                total_invested += investment_amount
                total_shares += shares_bought
                
                investments.append({
                    'date': date,
                    'price': row['Close'],
                    'ma20': row['MA20'],
                    'investment': investment_amount,
                    'shares_bought': shares_bought,
                    'total_invested': total_invested,
                    'total_shares': total_shares,
                    'current_value': total_shares * row['Close'],
                    'return_pct': (total_shares * row['Close'] - total_invested) / total_invested * 100
                })
    
    # 转换为DataFrame并保存结果
    results = pd.DataFrame(investments)
    results.to_csv('backtest_results.csv', index=False)
    
    # 打印最终结果
    final_value = total_shares * df['Close'][-1]
    total_return = (final_value - total_invested) / total_invested * 100
    
    print(f"\n=== 回测结果 ===")
    print(f"总投资金额: ${total_invested:,.2f}")
    print(f"最终市值: ${final_value:,.2f}")
    print(f"总收益率: {total_return:.2f}%")
    print(f"持有股数: {total_shares:.2f}")
    print(f"投资次数: {len(investments)}")
    
    # 在返回结果之前添加可视化
    plot_backtest_results(df, investments)
    
    return results

if __name__ == "__main__":
    backtest_strategy()