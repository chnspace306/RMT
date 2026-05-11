import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

def generate_sp500_rmt_dataset():
    print("🚀 正在初始化 S&P 500 5年期动态数据集获取向导...")
    
    # 1. 设定时间范围：固定截止到 2026-03-23，往回推 5 年
    end_date = datetime(2026, 3, 23)
    start_date = end_date - timedelta(days=365 * 5)
    print(f"📅 截取时间窗口: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    # 2. 选取标普500代表性股票池 (特别强化能源、军工与金融板块，以体现地缘冲突)
    tickers = [
        # --- 核心科技与消费 ---
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "PG", "KO", "PEP", 
        "WMT", "COST", "HD", "MCD", "DIS", "NFLX", "SBUX", "NKE",
        # --- 金融与投行 ---
        "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SPGI", "AXP", "V", "MA", "PYPL",
        # --- 医药健康 ---
        "JNJ", "UNH", "PFE", "ABBV", "LLY", "MRK", "TMO", "MDT",
        # --- 传统工业与制造业 ---
        "BA", "CAT", "MMM", "HON", "GE", "UNP", "UPS", "FDX", "CSX", "NSC", "WM", "RSG",
        # --- 📡 军工防务 (重点：俄乌/中东冲突受益方) ---
        "LMT", "RTX", "GD", "NOC", "TDG", "LHX", "HII",
        # --- 🛢️ 传统能源 (重点：油价波动核心标的) ---
        "XOM", "CVX", "COP", "SLB", "EOG", "OXY", "PXD", "MPC", "VLO",
        # --- 电信与公用事业 ---
        "T", "VZ", "NEE", "DUK", "SO", "EXC", "AEP", "SRE"
    ]
    
    print(f"📥 正在从 Yahoo Finance 下载 {len(tickers)} 只 S&P 500 股票的历史价格数据...")
    data = yf.download(tickers, start=start_date, end=end_date)['Close']
    
    print("🧹 正在进行数据清洗与计算每日对数收益率...")
    # 3. 计算对数收益率
    returns = np.log(data / data.shift(1))
    
    # 4. 数据清洗 
    returns = returns.dropna(axis=1, thresh=int(len(returns) * 0.9))
    returns = returns.ffill().fillna(0)
    returns = returns.dropna(axis=0)
    
    # 5. ✨ 保留时间戳 (Date)
    returns.reset_index(inplace=True)
    if 'index' in returns.columns:
        returns.rename(columns={'index': 'Date'}, inplace=True)
    if pd.api.types.is_datetime64_any_dtype(returns['Date']):
         returns['Date'] = returns['Date'].dt.strftime('%Y-%m-%d')
    
    # 6. 导出 CSV
    save_path = "sp500_real_returns_5yrs.csv" # 建议换个新名字以免覆盖老文件
    returns.to_csv(save_path, index=False)
    
    print(f"✅ 成功！S&P 500 数据集已生成: {save_path}")
    print(f"📊 最终规模: 样本数 N = {returns.shape[0]} 天, 特征维度 P = {returns.shape[1]-1}")

if __name__ == "__main__":
    generate_sp500_rmt_dataset()
