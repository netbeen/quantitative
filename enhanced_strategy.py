import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from data_fetcher import fetch_spy_historical_data

def calculate_technical_indicators(df):
    """计算技术指标"""
    # 计算多周期均线
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    # 计算波动率及其均值
    df['Daily_Return'] = df['Close'].pct_change()
    df['Volatility'] = df['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
    df['Volatility_MA'] = df['Volatility'].rolling(window=252).mean()
    
    # 计算RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算动量
    df['Momentum'] = df['Close'].pct_change(periods=20)
    
    return df

def calculate_investment_amount(row):
    """基于市场状态计算投资金额"""
    base_amount = 1000  # 基础投资金额
    multiplier = 1.0    # 基础乘数
    
    # 趋势判断（三均线多头排列给予加分）
    if row['MA20'] > row['MA50'] > row['MA200']:
        multiplier *= 1.5
    
    # 波动率策略（高波动率时加大投资）
    if row['Volatility'] > row['Volatility_MA']:
        vol_ratio = row['Volatility'] / row['Volatility_MA']
        multiplier *= min(vol_ratio, 2.0)
    
    # RSI策略（超卖区加大投资）
    if row['RSI'] < 30:
        multiplier *= 2.0
    elif row['RSI'] < 40:
        multiplier *= 1.5
    
    # 均值回归策略
    ma_deviation = (row['MA20'] - row['Close']) / row['MA20']
    if ma_deviation > 0.05:  # 价格显著低于MA20
        multiplier *= (1 + ma_deviation * 10)
    
    # 动量策略
    if row['Momentum'] < -0.05:  # 短期下跌超过5%
        multiplier *= 1.5
    
    # 计算最终投资金额（设置上限）
    investment = base_amount * multiplier
    return min(investment, 32000)  # 单次投资上限3.2万美元

def plot_backtest_results(df, investments):
    # 将投资记录转换为适合绘图的格式
    buy_dates = [pd.Timestamp(inv['date']) for inv in investments]
    buy_prices = [inv['price'] for inv in investments]
    buy_amounts = [inv['investment'] for inv in investments]
    
    # 准备投资金额数据
    investment_df = pd.DataFrame(index=df.index)
    investment_df['amount'] = 0
    for date, amount in zip(buy_dates, buy_amounts):
        investment_df.loc[date, 'amount'] = amount
    
    # 创建figure和子图
    fig = plt.figure(figsize=(15, 15))
    gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1], hspace=0.15)
    
    # 上方子图：价格和均线
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(df.index, df['Close'], label='Close', color='gray', alpha=0.6)
    ax1.plot(df.index, df['MA20'], label='MA20', color='orange')
    ax1.plot(df.index, df['MA50'], label='MA50', color='blue')
    ax1.plot(df.index, df['MA200'], label='MA200', color='red')
    
    # 添加买入点标记
    for date, price in zip(buy_dates, buy_prices):
        ax1.scatter(date, price, marker='^', color='green', s=100)
    
    ax1.set_title('SPY Enhanced Strategy Backtest')
    ax1.grid(True)
    ax1.legend()
    
    # 中间子图：RSI和波动率
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.plot(df.index, df['RSI'], label='RSI', color='purple')
    ax2.plot(df.index, df['Volatility'] * 100, label='Volatility%', color='orange')
    ax2.axhline(y=30, color='r', linestyle='--', alpha=0.5)
    ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5)
    ax2.set_title('Technical Indicators')
    ax2.grid(True)
    ax2.legend()
    
    # 下方子图：投资金额
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.bar(investment_df.index, investment_df['amount'], 
            color='blue', alpha=0.6, width=20)
    ax3.set_title('Investment Amount')
    ax3.set_ylabel('USD')
    ax3.grid(True)
    
    # 格式化y轴为美元格式
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # 调整x轴标签
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.setp(ax2.get_xticklabels(), visible=False)
    
    # 保存图表
    plt.savefig('enhanced_strategy_visualization.png', bbox_inches='tight', dpi=300)
    plt.close()

def backtest_strategy():
    # 获取数据并计算指标
    df = fetch_spy_historical_data()
    df = calculate_technical_indicators(df)
    
    # 设置回测起始时间（10年前）
    start_date = pd.Timestamp.now(tz='America/New_York') - pd.DateOffset(years=10)
    df = df[df.index >= start_date]
    
    # 初始化投资记录
    investments = []
    total_invested = 0
    total_shares = 0
    
    # 遍历每个交易日
    for date, row in df.iterrows():
        if date.day == 9 and not np.isnan(row['MA20']):
            investment_amount = calculate_investment_amount(row)
            shares_bought = investment_amount / row['Close']
            
            total_invested += investment_amount
            total_shares += shares_bought
            
            investments.append({
                'date': date,
                'price': row['Close'],
                'investment': investment_amount,
                'shares_bought': shares_bought,
                'total_invested': total_invested,
                'total_shares': total_shares,
                'current_value': total_shares * row['Close'],
                'return_pct': (total_shares * row['Close'] - total_invested) / total_invested * 100
            })
    
    # 转换为DataFrame并保存结果
    results = pd.DataFrame(investments)
    results.to_csv('enhanced_strategy_results.csv', index=False)
    
    # 打印最终结果
    final_value = total_shares * df['Close'][-1]
    total_return = (final_value - total_invested) / total_invested * 100
    
    print(f"\n=== Backtest Results ===")
    print(f"Total Investment: ${total_invested:,.2f}")
    print(f"Final Value: ${final_value:,.2f}")
    print(f"Total Return: {total_return:.2f}%")
    print(f"Shares Held: {total_shares:.2f}")
    print(f"Number of Investments: {len(investments)}")
    
    # 添加可视化
    plot_backtest_results(df, investments)
    
    return results

if __name__ == "__main__":
    backtest_strategy()