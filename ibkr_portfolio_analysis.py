from ib_insync import *
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

class IBKRPortfolioAnalyzer:
    def __init__(self):
        self.ib = IB()
        self.connect()
        
    def connect(self):
        """连接到IBKR TWS或IB Gateway"""
        try:
            self.ib.connect('127.0.0.1', 7497, clientId=1)  # TWS
        except ConnectionRefusedError:
            self.ib.connect('127.0.0.1', 4001, clientId=1)  # IB Gateway
            
    def fetch_trades(self):
        """获取所有已完成交易"""
        try:
            print("正在获取交易记录...")
            
            # 创建查询过滤器
            exec_filter = ExecutionFilter()
            # 设置开始时间为一年前
            one_year_ago = datetime.now() - timedelta(days=365)
            exec_filter.time = one_year_ago.strftime("%Y%m%d-%H:%M:%S")
            print(f"查询起始时间: {exec_filter.time}")
            
            # 等待连接就绪
            self.ib.sleep(1)
            
            # 请求交易记录
            trades = self.ib.reqExecutions(exec_filter)
            print(f"获取到 {len(trades)} 条交易记录")
            
            trade_records = []
            for trade in trades:
                trade_records.append({
                    'symbol': trade.execution.contract.symbol,
                    'date': trade.execution.time,
                    'side': trade.execution.side,
                    'quantity': trade.execution.shares,
                    'price': trade.execution.price,
                    'value': trade.execution.price * trade.execution.shares,
                    'commission': trade.commissionReport.commission
                })
                
            return pd.DataFrame(trade_records)
        except Exception as e:
            print(f"获取交易记录时出错: {e}")
            print("请检查 TWS 设置:")
            print("1. 确保 TWS 已启动并登录")
            print("2. 在 TWS 中启用 API 连接")
            print("3. 在 TWS 的 Global Configuration -> API -> Settings 中允许执行和交易数据访问")
            return pd.DataFrame()
    
    def get_current_price_and_ma20(self, symbol):
        """获取当前价格和20日均线"""
        try:
            # 获取股票数据
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1mo')  # 获取一个月数据用于计算MA20
            
            if len(hist) > 0:
                current_price = hist['Close'].iloc[-1]  # 使用 iloc 替代 []
                ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]  # 使用 iloc 替代 []
                return current_price, ma20
            return None, None
        except:
            return None, None
    
    def get_current_positions(self):
        """获取当前持仓信息"""
        positions = self.ib.positions()
        
        position_records = []
        for pos in positions:
            contract = pos.contract
            
            # 获取当前价格和MA20
            current_price, ma20 = self.get_current_price_and_ma20(contract.symbol)
            if current_price is None:
                current_price = pos.avgCost
            
            avg_cost = pos.avgCost
            quantity = pos.position
            market_value = current_price * quantity
            cost_basis = avg_cost * quantity
            unrealized_pnl = market_value - cost_basis
            pnl_percentage = (unrealized_pnl / cost_basis) * 100 if cost_basis != 0 else 0
            
            position_records.append({
                'symbol': contract.symbol,
                'quantity': quantity,
                'avg_cost': avg_cost,
                'current_price': current_price,
                'ma20': ma20 if ma20 is not None else avg_cost,
                'market_value': market_value,
                'cost_basis': cost_basis,
                'unrealized_pnl': unrealized_pnl,
                'pnl_percentage': pnl_percentage
            })
            
        return pd.DataFrame(position_records)
    
    def analyze_portfolio(self):
        """分析投资组合表现"""
        trades_df = self.fetch_trades()
        positions_df = self.get_current_positions()
        
        # 打印交易历史统计
        print("\n=== 交易历史 ===")
        print(f"总交易次数: {len(trades_df)}")
        if not trades_df.empty:
            print(f"总交易金额: ${trades_df['value'].sum():,.2f}")
            print(f"总手续费: ${trades_df['commission'].sum():,.2f}")
        else:
            print("暂无交易记录")
        
        # 打印当前持仓状况
        print("\n=== 当前持仓 ===")
        for _, pos in positions_df.iterrows():
            print(f"\n{pos['symbol']}:")
            print(f"持仓数量: {pos['quantity']:.2f}")
            print(f"平均成本: ${pos['avg_cost']:.2f}")
            print(f"当前价格: ${pos['current_price']:.2f}")
            print(f"市值: ${pos['market_value']:,.2f}")
            print(f"未实现盈亏: ${pos['unrealized_pnl']:,.2f}")
            print(f"收益率: {pos['pnl_percentage']:.2f}%")
        
        # 计算组合总体情况
        total_value = positions_df['market_value'].sum()
        total_cost = positions_df['cost_basis'].sum()
        total_pnl = positions_df['unrealized_pnl'].sum()
        total_pnl_percentage = (total_pnl / total_cost) * 100 if total_cost != 0 else 0
        
        print("\n=== 组合总览 ===")
        print(f"总市值: ${total_value:,.2f}")
        print(f"总成本: ${total_cost:,.2f}")
        print(f"总未实现盈亏: ${total_pnl:,.2f}")
        print(f"组合收益率: {total_pnl_percentage:.2f}%")
    
    def __del__(self):
        """断开连接"""
        if self.ib.isConnected():
            self.ib.disconnect()

if __name__ == "__main__":
    analyzer = IBKRPortfolioAnalyzer()
    analyzer.analyze_portfolio()