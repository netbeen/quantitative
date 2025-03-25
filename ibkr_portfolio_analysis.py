from ib_insync import *
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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
        trades = self.ib.reqExecutions()
        
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
    
    def get_current_positions(self):
        """获取当前持仓信息（使用成本价替代市场价）"""
        positions = self.ib.positions()
        
        position_records = []
        for pos in positions:
            contract = pos.contract
            
            # 使用持仓成本价替代市场价
            current_price = pos.avgCost
            avg_cost = pos.avgCost
            quantity = pos.position
            market_value = current_price * quantity
            cost_basis = avg_cost * quantity
            unrealized_pnl = market_value - cost_basis  # 这里会是0，因为使用了相同的价格
            pnl_percentage = 0  # 同样会是0
            
            position_records.append({
                'symbol': contract.symbol,
                'quantity': quantity,
                'avg_cost': avg_cost,
                'current_price': current_price,
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