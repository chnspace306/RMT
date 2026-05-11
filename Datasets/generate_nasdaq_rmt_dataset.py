import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import os

def generate_nasdaq_rmt_dataset():
    print("🚀 正在初始化 NASDAQ 5年期动态数据集获取向导...")
    
    # 1. 设定时间范围：固定截止到 2026-03-23，往回推 5 年
    end_date = datetime(2026, 3, 23)
    start_date = end_date - timedelta(days=365 * 5)
    print(f"📅 截取时间窗口: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    # 2. 选取纳斯达克代表性股票池 (约100只核心科技与成长股)
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AVGO", "ADBE", "AMD",
        "INTC", "QCOM", "TXN", "MU", "MRVL", "LRCX", "KLAC", "AMAT", "ASML", "CRM", 
        "ORCL", "NOW", "SNOW", "PANW", "CRWD", "ZS", "DDOG", "NET", "TEAM", "NFLX", 
        "ABNB", "BKNG", "MELI", "PDD", "JD", "CPNG", "SE", "DASH", "UBER", "PYPL", 
        "SQ", "COIN", "HOOD", "AFRM", "UPST", "SOFI", "ROKU", "SPOT", "TTD", "PINS", 
        "SNAP", "MTCH", "ZM", "DOCN", "FSLR", "ENPH", "SEDG", "PLUG", "RUN", "AMGN", 
        "GILD", "REGN", "VRTX", "BIIB", "ILMN", "IDXX", "ALGN", "DXCM", "PODD", "ISRG",
        "COST", "PEP", "SBUX", "MDLZ", "KHC", "MNST", "KDP", "LULU", "MAR", "ORLY", 
        "PCAR", "MCHP", "FTNT", "WDAY", "LSCC", "SWKS", "ON", "XEL", "EXC", "AEP", 
        "CEG", "BKR", "FANG", "GEHC", "CTAS", "ARM", "PLTR", "AI", "SMCI"
    ]
    
    print(f"📥 正在从 Yahoo Finance 下载 {len(tickers)} 只 NASDAQ 股票的历史价格数据...")
    data = yf.download(tickers, start=start_date, end=end_date)['Close']
    
    print("🧹 正在进行数据清洗与计算每日对数收益率...")
    # 3. 计算对数收益率
    returns = np.log(data / data.shift(1))
    
    # 4. 数据清洗 (剔除上市不满 5 年或数据缺失严重的标的)
    returns = returns.dropna(axis=1, thresh=int(len(returns) * 0.9))
    returns = returns.ffill().fillna(0)
    returns = returns.dropna(axis=0)
    
    # 5. ✨ 保留时间戳 (Date) 以支持系统的动态滑动窗口机制
    returns.reset_index(inplace=True)
    if 'index' in returns.columns:
        returns.rename(columns={'index': 'Date'}, inplace=True)
    if pd.api.types.is_datetime64_any_dtype(returns['Date']):
         returns['Date'] = returns['Date'].dt.strftime('%Y-%m-%d')
    
    # 6. 导出 CSV
    save_path = "nasdaq_real_returns_5yrs.csv" # 建议换个新名字以免覆盖老文件
    returns.to_csv(save_path, index=False)
    
    print(f"✅ 成功！NASDAQ 数据集已生成: {save_path}")
    print(f"📊 最终规模: 样本数 N = {returns.shape[0]} 天, 特征维度 P = {returns.shape[1]-1}")

if __name__ == "__main__":
    generate_nasdaq_rmt_dataset()
