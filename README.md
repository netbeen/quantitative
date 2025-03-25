# IBKR Portfolio Analyzer

基于 Interactive Brokers (IBKR) API 的投资组合分析工具，用于实时监控和分析 IBKR 账户中的持仓情况。

## 功能特性

- 实时获取 IBKR 账户持仓信息
- 计算每个持仓的当前市值和盈亏情况
- 获取股票的实时价格和 20 日均线数据
- 分析整体投资组合表现
- 查看历史交易记录

## 环境要求

- Python 3.7+
- IBKR Trader Workstation (TWS) 或 IB Gateway
- TWS/IB Gateway API 权限已启用

## 依赖安装

```bash
pip install ib_insync pandas numpy yfinance
```