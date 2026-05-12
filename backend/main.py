import matplotlib
matplotlib.use('Agg')
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
# 彻底移除 pandas 依赖以解决导入挂起问题
import io
import os
import warnings
import csv as csv_mod
import base64

from backend.schemas import WignerRequest, WignerResponse, TheoreticalCurve, MPRequest, MPResponse, AnalyzeRequest, OutlierEigenvector, TopComponent, RollingResponse, HeatmapResponse
from backend.rmt_core import generate_goe_eigenvalues, wigner_semicircle_pdf, generate_mp_eigenvalues, mp_pdf

app = FastAPI(title="RMT Backend API (No-Pandas Edition)", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== 辅助函数：原生 CSV 处理 ======

def native_load_csv(content_stream):
    """使用原生 csv 模块读取数据，返回 (headers, data_rows)"""
    reader = csv_mod.reader(content_stream)
    try:
        headers = next(reader)
    except StopIteration:
        return [], []
    
    rows = []
    for row in reader:
        if any(row): # 忽略空行
            rows.append(row)
    return headers, rows

def extract_time_labels_native(headers, rows):
    """
    原生实现的时间列识别逻辑
    返回 (time_labels, numeric_matrix, remaining_headers)
    """
    time_keywords = ['date', 'time', 'timestamp', 'year', 'month', 'day', '日期', '时间', '成交日期', 'datetime', 'period', 'unnamed: 0', 'index']
    
    time_col_idx = -1
    # 1. 关键字匹配
    for i, h in enumerate(headers):
        if any(k in h.lower() for k in time_keywords):
            time_col_idx = i
            break
            
    # 2. 如果没匹配到，看第一列是否为非数值
    if time_col_idx == -1 and len(rows) > 0:
        try:
            float(rows[0][0])
        except (ValueError, IndexError):
            time_col_idx = 0
            
    time_labels = []
    numeric_data = []
    new_headers = []
    
    for i, h in enumerate(headers):
        if i != time_col_idx:
            new_headers.append(h)
            
    for row in rows:
        if time_col_idx != -1:
            time_labels.append(row[time_col_idx])
            numeric_row = [row[j] for j in range(len(row)) if j != time_col_idx]
        else:
            numeric_row = row
            
        # 尝试转为 float
        cleaned_row = []
        for val in numeric_row:
            try:
                cleaned_row.append(float(val))
            except ValueError:
                cleaned_row.append(np.nan)
        numeric_data.append(cleaned_row)
        
    return time_labels, np.array(numeric_data), new_headers

# ====== 核心逻辑：分析与处理 ======

def process_matrix(mat, headers, scale, fill_strategy, standardize, time_labels=[]):
    """统一的矩阵分析引擎 (Numpy 原生版)"""
    n, p = mat.shape
    if n == 0 or p == 0:
        raise HTTPException(status_code=400, detail="Empty numeric matrix")

    # 填充策略
    if fill_strategy == 'mean':
        col_means = np.nanmean(mat, axis=0)
        col_means = np.nan_to_num(col_means, nan=0.0)
        for i in range(p):
            mask = np.isnan(mat[:, i])
            mat[mask, i] = col_means[i]
    else:
        mat = np.nan_to_num(mat, nan=0.0)

    sparsity = 1.0 - (np.count_nonzero(mat) / mat.size) if mat.size > 0 else 0.0
    
    if standardize:
        means = np.mean(mat, axis=0)
        stds = np.std(mat, axis=0)
        stds[stds == 0] = 1.0
        mat = (mat - means) / stds
        sigma_sq = 1.0
    else:
        sigma_sq = scale ** 2

    q = p / n if n > 0 else 1.0
    centered = mat - np.mean(mat, axis=0)
    C = (1.0 / n) * np.dot(centered.T, centered)
    eigenvalues, eigenvectors = np.linalg.eigh(C)
    
    lambda_plus = sigma_sq * (1 + np.sqrt(q))**2
    lambda_minus = sigma_sq * (1 - np.sqrt(q))**2
    
    outlier_eigenvectors = []
    sorted_indices = np.argsort(eigenvalues)[::-1]
    rank = 0
    for idx in sorted_indices:
        ev = float(eigenvalues[idx])
        if ev <= lambda_plus: break
        rank += 1
        vec = eigenvectors[:, idx]
        abs_vec = np.abs(vec)
        top_k = min(5, len(vec))
        top_indices = np.argsort(abs_vec)[::-1][:top_k]
        
        components = []
        for ci in top_indices:
            name = headers[int(ci)] if int(ci) < len(headers) else f"Col_{int(ci)}"
            components.append(TopComponent(column_index=int(ci), column_name=name, weight=float(vec[ci]), abs_weight=float(abs_vec[ci])))
        
        outlier_eigenvectors.append(OutlierEigenvector(eigenvalue=ev, rank=rank, top_components=components, vector=[float(v) for v in vec]))
        if rank >= 10: break

    # IPR
    ipr = np.sum(eigenvectors**4, axis=0).tolist()
    
    # 降噪热力图生成 (Numpy 原生版)
    cleaned_heatmap_base64 = None
    try:
        # 识别信号成分
        signal_indices = np.where(eigenvalues > lambda_plus)[0]
        if len(signal_indices) > 0:
            bulk_indices = np.where(eigenvalues <= lambda_plus)[0]
            avg_bulk_ev = np.mean(eigenvalues[bulk_indices]) if len(bulk_indices) > 0 else 0
            
            # 重构相关系数矩阵
            C_clean = np.zeros_like(C)
            for i in range(len(eigenvalues)):
                ev = eigenvalues[i] if i in signal_indices else avg_bulk_ev
                v = eigenvectors[:, i:i+1]
                C_clean += ev * np.dot(v, v.T)
            
            # 归一化为相关系数矩阵（对角线为1）
            d = np.sqrt(np.diag(C_clean))
            d[d == 0] = 1.0
            C_clean = C_clean / np.outer(d, d)
        else:
            C_clean = C

        import matplotlib.pyplot as plt
        plt.style.use('dark_background')
        fig, axes = plt.subplots(1, 2, figsize=(10, 4), facecolor='#1c1c1e')
        
        im0 = axes[0].imshow(C, cmap='coolwarm', vmin=-1, vmax=1)
        axes[0].set_title('Original Correlation', color='white', fontsize=10)
        axes[0].axis('off')
        
        im1 = axes[1].imshow(C_clean, cmap='coolwarm', vmin=-1, vmax=1)
        axes[1].set_title('RMT Cleaned', color='white', fontsize=10)
        axes[1].axis('off')
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close(fig)
        buf.seek(0)
        cleaned_heatmap_base64 = "data:image/png;base64," + base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        print(f"Heatmap generation error: {e}")

    # 理论曲线
    x_start = max(0.01, lambda_minus - 0.5 * sigma_sq)
    x_end = lambda_plus + 0.5 * sigma_sq
    x_theory = np.linspace(x_start, x_end, 200)
    y_theory = mp_pdf(x_theory, q, sigma_sq)
    
    return MPResponse(
        q=q, lambda_plus=lambda_plus, lambda_minus=lambda_minus,
        eigenvalues=eigenvalues.tolist(),
        theoretical_curve=TheoreticalCurve(x=x_theory.tolist(), y=y_theory.tolist()),
        sparsity=sparsity, n=n, p=p,
        outlier_eigenvectors=outlier_eigenvectors, column_names=headers,
        time_labels=time_labels, ipr=ipr, cleaned_heatmap_base64=cleaned_heatmap_base64
    )


# ====== 路由接口 ======

@app.get("/")
def health_check():
    return {"status": "ok", "mode": "no-pandas"}

def get_datasets_dir():
    search_dirs = [os.path.join(os.path.dirname(__file__), "Datasets"), "backend/Datasets", "Datasets"]
    for d in search_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            return os.path.abspath(d)
    return None

@app.get("/api/rmt/examples")
async def list_examples():
    d = get_datasets_dir()
    if not d: return []
    return [f for f in os.listdir(d) if f.endswith('.csv')]

@app.post("/api/rmt/use_example", response_model=MPResponse)
async def use_example(name: str = Form(...), scale: float = Form(1.0), fill_strategy: str = Form("zero"), standardize: str = Form("true"), start_row: int = Form(0), end_row: int = Form(-1)):
    d = get_datasets_dir()
    if not d: raise HTTPException(status_code=404)
    file_path = os.path.join(d, name)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        headers, rows = native_load_csv(f)
    
    time_labels, mat, numeric_headers = extract_time_labels_native(headers, rows)
    
    # 切片
    if end_row == -1: end_row = len(mat)
    mat = mat[start_row:end_row]
    slice_labels = time_labels[start_row:end_row] if time_labels else []
    
    is_std = standardize.lower() == "true"
    return process_matrix(mat, numeric_headers, scale, fill_strategy, is_std, time_labels) # 返回全量时间标签以供滑动条

@app.post("/api/rmt/upload", response_model=MPResponse)
async def upload_matrix(file: UploadFile = File(...), scale: float = Form(...), fill_strategy: str = Form("zero"), standardize: str = Form("true"), start_row: int = Form(0), end_row: int = Form(-1)):
    contents = await file.read()
    f = io.StringIO(contents.decode("utf-8"))
    headers, rows = native_load_csv(f)
    time_labels, mat, numeric_headers = extract_time_labels_native(headers, rows)
    
    if end_row == -1: end_row = len(mat)
    mat = mat[start_row:end_row]
    
    is_std = standardize.lower() == "true"
    return process_matrix(mat, numeric_headers, scale, fill_strategy, is_std, time_labels)

@app.post("/api/rmt/wigner", response_model=WignerResponse)
def get_wigner_data(req: WignerRequest):
    eigenvalues = generate_goe_eigenvalues(req.n, req.scale)
    r = 2 * req.scale * np.sqrt(req.n)
    x_theory = np.linspace(-r * 1.1, r * 1.1, 500)
    y_theory = wigner_semicircle_pdf(x_theory, r)
    return WignerResponse(eigenvalues=eigenvalues.tolist(), theoretical_curve=TheoreticalCurve(x=x_theory.tolist(), y=y_theory.tolist()))

@app.post("/api/rmt/mp", response_model=MPResponse)
def get_mp_data(req: MPRequest):
    q = req.p / req.n
    sigma_sq = req.scale ** 2
    eigenvalues = generate_mp_eigenvalues(req.n, req.p, req.scale)
    lambda_plus = sigma_sq * (1 + np.sqrt(q))**2
    lambda_minus = sigma_sq * (1 - np.sqrt(q))**2
    x_theory = np.linspace(max(0.01, lambda_minus-0.5), lambda_plus+0.5, 200)
    y_theory = mp_pdf(x_theory, q, sigma_sq)
    return MPResponse(q=q, lambda_plus=lambda_plus, lambda_minus=lambda_minus, eigenvalues=eigenvalues.tolist(), theoretical_curve=TheoreticalCurve(x=x_theory.tolist(), y=y_theory.tolist()))

@app.post("/api/rmt/analyze")
async def analyze_rmt(req: AnalyzeRequest):
    """AI 分析接口：基于 OpenAI SDK 的流式返回"""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=req.api_key if req.api_key else "sk-none", base_url=req.base_url)
        
        eigvec_section = f"\n【特征向量分析】\n{req.eigenvector_summary}" if req.eigenvector_summary else ""
        prompt = f"请作为金融随机矩阵理论专家，分析数据集 {req.dataset_name}。数据维度 q={req.q:.4f}, 异常值数量={req.outlier_count}。核心特征值: {req.top_eigenvalues}. {eigvec_section}"
        
        async def stream_generator():
            try:
                stream = await client.chat.completions.create(
                    model=req.model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的金融随机矩阵理论 (RMT) 分析助手。请根据提供的特征值和维度信息，分析市场的相关性结构、是否存在显著的集体行为（市场模态）以及噪声水平。"},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as e:
                yield f"AI 分析生成失败: {str(e)}"
        
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI 模块调用失败: {str(e)}")

# ====== 滚动分析逻辑 (Numpy 原生版) ======


def run_rolling_analysis_logic(headers, rows, window_size, step_size, standardize):
    """滚动分析的原生 Numpy 实现"""
    times, mat, _ = extract_time_labels_native(headers, rows)
    if not times:
        times = [str(i) for i in range(len(rows))]
    
    n, p = mat.shape
    if n < window_size:
        raise HTTPException(status_code=400, detail=f"Dataset rows ({n}) less than window size ({window_size})")

    is_std = standardize.lower() == "true"
    res_times, res_l1 = [], []
    
    # 遍历滑动窗口
    for start in range(0, n - window_size + 1, step_size):
        end = start + window_size
        win = mat[start:end, :]
        
        # 填充 NaN
        win = np.nan_to_num(win, nan=0.0)
        
        if is_std:
            means = np.mean(win, axis=0)
            stds = np.std(win, axis=0)
            stds[stds == 0] = 1.0
            win = (win - means) / stds
            
        centered = win - np.mean(win, axis=0)
        C = (1.0 / window_size) * np.dot(centered.T, centered)
        evs = np.linalg.eigvalsh(C)
        res_l1.append(float(np.max(evs)))
        # 时间戳取窗口终点
        res_times.append(times[min(end-1, len(times)-1)])
        
    return RollingResponse(times=res_times, lambda_1=res_l1)

@app.post("/api/rmt/rolling", response_model=RollingResponse)
async def analyze_rolling(file: UploadFile = File(...), window_size: int = Form(60), step_size: int = Form(1), standardize: str = Form("true")):
    contents = await file.read()
    f = io.StringIO(contents.decode("utf-8"))
    headers, rows = native_load_csv(f)
    return run_rolling_analysis_logic(headers, rows, window_size, step_size, standardize)

@app.post("/api/rmt/rolling_example", response_model=RollingResponse)
async def rolling_example(name: str = Form(...), window_size: int = Form(60), step_size: int = Form(1), standardize: str = Form("true")):
    d = get_datasets_dir()
    if not d: raise HTTPException(status_code=404)
    file_path = os.path.join(d, name)
    with open(file_path, 'r', encoding='utf-8') as f:
        headers, rows = native_load_csv(f)
    return run_rolling_analysis_logic(headers, rows, window_size, step_size, standardize)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8888)

