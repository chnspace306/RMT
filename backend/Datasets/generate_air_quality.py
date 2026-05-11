import pandas as pd
import numpy as np
import os

def generate_air_quality_dataset():
    np.random.seed(42)
    n_days = 250
    n_stations = 32
    
    # 1. 基础随机噪声 (符合 RMT 的 Bulk 部分)
    noise = np.random.normal(0, 1, (n_days, n_stations))
    
    # 2. 全局大气模式 (Market Mode / Common Factor)
    global_trend = np.random.normal(0, 1, (n_days, 1))
    global_weights = np.random.uniform(0.5, 1.5, (1, n_stations))
    global_signal = np.dot(global_trend, global_weights)
    
    # 3. 局部工业区污染源 (Local Factor / Sector Mode)
    local_event = np.zeros((n_days, n_stations))
    industrial_trend = np.random.normal(0, 1, (n_days, 1))
    local_event[:, 10:16] = industrial_trend * 2.0
    
    # 合并数据
    data = global_signal + local_event + noise
    
    # 创建日期列
    dates = pd.date_range(start='2023-01-01', periods=n_days)
    
    # 转换为 DataFrame
    station_names = [f"Station_{i+1:02d}" for i in range(n_stations)]
    df = pd.DataFrame(data, columns=station_names)
    df.insert(0, 'Date', dates.strftime('%Y-%m-%d'))
    
    # 保存到 Datasets 目录
    target_path = r'd:\毕业论文\毕业设计\backend\Datasets\air_quality_multi_station.csv'
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    df.to_csv(target_path, index=False)
    print(f"Air quality dataset generated at {target_path}")

if __name__ == "__main__":
    generate_air_quality_dataset()
