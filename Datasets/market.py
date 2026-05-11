import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import os

def generate_large_scale_rmt_dataset():
    print("🚀 正在初始化 RMT 大规模多维时序数据集获取程序...")
    
    # 1. 设定时间范围：过去 3 年（保证 N > P，符合大维随机矩阵条件）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 3)
    
    # 2. 构建扩展股票池与宏观因子池 (P 维度扩展)
    # 包含：科技巨头、半导体、医药、金融、能源、消费 以及 核心宏观指标
    stock_tickers = [
        # --- 科技与互联网 ---
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NFLX", "ADBE", "CRM", "ORCL",
        # --- 半导体与硬件 ---
        "NVDA", "AMD", "INTC", "QCOM", "AVGO", "TXN", "MU", "AMAT", "ASML", "LRCX",
        # --- 金融与支付 ---
        "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "PYPL", "AXP",
        # --- 医药与健康 ---
        "JNJ", "UNH", "PFE", "ABBV", "LLY", "MRK", "TMO", "MDT", "BMY", "AMGN",
        # --- 能源与工业 ---
        "XOM", "CVX", "COP", "SLB", "EOG", "BA", "CAT", "GE", "HON", "LMT", "RTX",
        # --- 消费与零售 ---
        "WMT", "COST", "HD", "MCD", "NKE", "SBUX", "KO", "PEP", "PG", "PM",
        # --- 通信与公用事业 ---
        "T", "VZ", "CMCSA", "DIS", "NEE", "DUK", "SO", "EXC", "AEP", "SRE"
    ]
    
    # 宏观指标（雅虎财经代码）
    macro_tickers = [
        "^VIX",   # CBOE 市场恐慌指数
        "^TNX",   # 美国10年期国债收益率
        "CL=F",   # WTI 原油连续合约
        "GC=F"    # 黄金连续合约
    ]
    
    all_tickers = stock_tickers + macro_tickers
    print(f"📥 正在从 Yahoo Finance 下载 {len(all_tickers)} 个维度的历史数据...")
    
    # 3. 下载数据 (获取每日收盘价)
    data = yf.download(all_tickers, start=start_date, end=end_date)['Close']
    
    print("🧹 正在进行数据清洗与对数收益率计算...")
    
    # 4. 数据清洗与计算
    # 计算每日对数收益率: ln(P_t / P_{t-1})
    returns = np.log(data / data.shift(1))
    
    # 清洗：去除缺失值超过 10% 的列 (剔除上市时间过短或数据不全的标的)
    returns = returns.dropna(axis=1, thresh=int(len(returns) * 0.9))
    
    # 清洗：由于宏观期货和股票的交易日可能存在极小差异，使用前向填充处理少量空值
    returns = returns.ffill().fillna(0)
    
    # 清洗：删除第一行 (因为 shift(1) 导致第一行必定是 NaN)
    returns = returns.dropna(axis=0)
    
    # 5. ✨ 核心步骤：保留时间戳作为实体数据列 ✨
    # 将原本作为索引的日期 (DatetimeIndex) 转换为名为 'Date' 的一列
    returns.reset_index(inplace=True)
    if 'index' in returns.columns:
        returns.rename(columns={'index': 'Date'}, inplace=True)
    
    # 格式化日期列，只保留 YYYY-MM-DD，去掉时分秒（如果存在的话）
    if pd.api.types.is_datetime64_any_dtype(returns['Date']):
         returns['Date'] = returns['Date'].dt.strftime('%Y-%m-%d')
    
    # 6. 保存至指定的绝对路径
    save_dir = r"D:\毕业论文\毕业设计\Datasets"
    save_path = os.path.join(save_dir, "extended_market_returns.csv")
    
    # 检查文件夹是否存在，不存在则自动创建
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"📁 目录不存在，已自动创建: {save_dir}")
        
    returns.to_csv(save_path, index=False)
    
    print(f"✅ 成功！数据集已保存至: {save_path}")
    print(f"📊 数据集规模: 样本数 N = {returns.shape[0]} (天), 特征维度 P = {returns.shape[1]-1} (资产)")

if __name__ == "__main__":
    generate_large_scale_rmt_dataset()