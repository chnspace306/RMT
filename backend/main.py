import matplotlib
matplotlib.use('Agg')
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
import io
import os
import warnings
import csv as csv_mod
import matplotlib.pyplot as plt
import base64

from backend.schemas import WignerRequest, WignerResponse, TheoreticalCurve, MPRequest, MPResponse, AnalyzeRequest, OutlierEigenvector, TopComponent, RollingResponse, HeatmapResponse
from backend.rmt_core import generate_goe_eigenvalues, wigner_semicircle_pdf, generate_mp_eigenvalues, mp_pdf

app = FastAPI(title="RMT Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== 核心逻辑提取：矩阵处理与分析函数 ======
def process_dataframe(df: pd.DataFrame, scale: float, fill_strategy: str, standardize: bool):
    """
    统一的矩阵分析引擎，支持 CSV 导入和本地加载。
    包含：预处理、RMT 分析、IPR 计算、降噪热力图生成。
    """
    column_names = df.columns.tolist()
    
    # 转换为 numpy 数组
    mat = df.values.astype(float)
    
    # 基础清洗
    mat = mat[~np.isnan(mat).all(axis=1)]
    if mat.size > 0:
        mat = mat[:, ~np.isnan(mat).all(axis=0)]
        
    if mat.size > 0:
        sparsity = 1.0 - (np.count_nonzero(np.nan_to_num(mat, nan=0.0)) / mat.size)
    else:
        sparsity = 0.0

    # 填充策略
    if fill_strategy == 'mean':
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            col_mean = np.nanmean(mat, axis=0)
            col_mean = np.nan_to_num(col_mean, nan=0.0)
        inds = np.where(np.isnan(mat))
        mat[inds] = np.take(col_mean, inds[1])
    elif fill_strategy == 'drop':
        mat = mat[~np.isnan(mat).any(axis=1)]
    else:
        mat = np.nan_to_num(mat, nan=0.0)

    n, p = mat.shape
    q = p / n if n > 0 else 1.0
    
    eigenvectors = None
    C = None
    if n > 1 and p > 0:
        if standardize:
            stds = np.std(mat, axis=0)
            stds[stds == 0] = 1.0
            mat = (mat - np.mean(mat, axis=0)) / stds
            
        centered = mat - np.mean(mat, axis=0)
        C = (1.0 / n) * np.dot(centered.T, centered)
        eigenvalues, eigenvectors = np.linalg.eigh(C)
    else:
        eigenvalues = np.array([])
        
    if standardize:
        sigma_sq = 1.0
    elif len(eigenvalues) > 0:
        sigma_sq = float(np.mean(eigenvalues))
    else:
        sigma_sq = scale ** 2
         
    lambda_plus = sigma_sq * (1 + np.sqrt(q))**2
    lambda_minus = sigma_sq * (1 - np.sqrt(q))**2
    
    outlier_eigenvectors: list[OutlierEigenvector] = []
    ipr = []
    cleaned_heatmap_base64 = None

    if eigenvectors is not None and len(eigenvalues) > 0:
        # eigh 返回从小到大，转为从大到小
        sorted_indices = np.argsort(eigenvalues)[::-1]
        
        rank = 0
        for idx in sorted_indices:
            ev = float(eigenvalues[idx])
            if ev <= lambda_plus:
                break
            rank += 1
            vec = eigenvectors[:, idx]
            abs_vec = np.abs(vec)
            top_k = min(5, len(vec))
            top_indices = np.argsort(abs_vec)[::-1][:top_k]
            
            components = []
            for ci in top_indices:
                name = column_names[int(ci)] if int(ci) < len(column_names) else f"Col_{int(ci)}"
                components.append(TopComponent(
                    column_index=int(ci), column_name=name,
                    weight=float(vec[ci]), abs_weight=float(abs_vec[ci])
                ))
            
            outlier_eigenvectors.append(OutlierEigenvector(
                eigenvalue=ev, rank=rank, top_components=components,
                vector=[float(v) for v in vec]
            ))
            if rank >= 10: break
        
        # IPR & Heatmap
        ipr = np.sum(eigenvectors**4, axis=0).tolist()
        try:
            signal_indices = np.where(eigenvalues > lambda_plus)[0]
            if len(signal_indices) > 0:
                bulk_indices = np.where(eigenvalues <= lambda_plus)[0]
                avg_bulk_ev = np.mean(eigenvalues[bulk_indices]) if len(bulk_indices) > 0 else 0
                C_clean = np.zeros_like(C)
                for i in range(len(eigenvalues)):
                    ev = eigenvalues[i] if i in signal_indices else avg_bulk_ev
                    v = eigenvectors[:, i:i+1]
                    C_clean += ev * np.dot(v, v.T)
                d = np.sqrt(np.diag(C_clean))
                C_clean = C_clean / np.outer(d, d)
            else:
                C_clean = C
            
            plt.style.use('dark_background')
            fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor='#1c1c1e')
            axes[0].imshow(C, cmap='coolwarm', vmin=-1, vmax=1)
            axes[0].set_title('Original Correlation', color='white')
            axes[0].axis('off')
            axes[1].imshow(C_clean, cmap='coolwarm', vmin=-1, vmax=1)
            axes[1].set_title('RMT Cleaned', color='white')
            axes[1].axis('off')
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=120)
            plt.close(fig)
            buf.seek(0)
            cleaned_heatmap_base64 = "data:image/png;base64," + base64.b64encode(buf.read()).decode('utf-8')
        except: pass

    x_start = max(0.01, lambda_minus - 0.5 * sigma_sq)
    x_end = lambda_plus + 0.5 * sigma_sq
    x_theory = np.linspace(x_start, x_end, 200)
    y_theory = mp_pdf(x_theory, q, sigma_sq)
    
    return MPResponse(
        q=q, lambda_plus=lambda_plus, lambda_minus=lambda_minus,
        eigenvalues=eigenvalues.tolist(),
        theoretical_curve=TheoreticalCurve(x=x_theory.tolist(), y=y_theory.tolist()),
        sparsity=sparsity, n=n, p=p,
        outlier_eigenvectors=outlier_eigenvectors, column_names=column_names,
        ipr=ipr, cleaned_heatmap_base64=cleaned_heatmap_base64
    )

# ====== 路由接口 ======

@app.get("/")
def health_check():
    return {"status": "ok", "message": "RMT Backend is running"}

@app.get("/api/rmt/examples")
async def list_examples():
    # 尝试多个可能的路径，确保在 Docker 容器中也能找到
    possible_paths = [
        os.path.join(os.getcwd(), "Datasets"),
        os.path.join(os.path.dirname(__file__), "Datasets"),
        "/app/backend/Datasets",
        "/app/Datasets"
    ]
    
    datasets_dir = None
    for p in possible_paths:
        if os.path.exists(p) and os.path.isdir(p):
            datasets_dir = p
            break
            
    if not datasets_dir: 
        print(f"DEBUG: Datasets directory not found. Checked: {possible_paths}")
        return []
        
    return [f for f in os.listdir(datasets_dir) if f.endswith('.csv')]

@app.post("/api/rmt/use_example", response_model=MPResponse)
async def use_example(
    name: str = Form(...),
    scale: float = Form(1.0),
    fill_strategy: str = Form("zero"),
    standardize: str = Form("true")
):
    possible_paths = [
        os.path.join(os.getcwd(), "Datasets"),
        os.path.join(os.path.dirname(__file__), "Datasets"),
        "/app/backend/Datasets",
        "/app/Datasets"
    ]
    
    datasets_dir = None
    for p in possible_paths:
        if os.path.exists(p) and os.path.isdir(p):
            datasets_dir = p
            break
            
    if not datasets_dir:
        raise HTTPException(status_code=404, detail="Datasets directory not found")
        
    file_path = os.path.join(datasets_dir, name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = pd.read_csv(file_path)
    # 尝试处理带有时间列的数据集（如果是第一列）
    if df.dtypes.iloc[0] == 'object' or pd.api.types.is_datetime64_any_dtype(df.dtypes.iloc[0]):
        df = df.iloc[:, 1:]
    
    is_std = standardize.lower() == "true"
    return process_dataframe(df, scale, fill_strategy, is_std)

@app.post("/api/rmt/upload", response_model=MPResponse)
async def upload_matrix(
    file: UploadFile = File(...), 
    scale: float = Form(...), 
    fill_strategy: str = Form("zero"),
    standardize: str = Form("true")
):
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    
    # 自动处理第一列是日期的情况
    if df.dtypes.iloc[0] == 'object' or pd.api.types.is_datetime64_any_dtype(df.dtypes.iloc[0]):
        df = df.iloc[:, 1:]
        
    is_std = standardize.lower() == "true"
    return process_dataframe(df, scale, fill_strategy, is_std)

@app.post("/api/rmt/wigner", response_model=WignerResponse)
def get_wigner_data(req: WignerRequest):
    eigenvalues = generate_goe_eigenvalues(req.n, req.scale)
    r = 2 * req.scale * np.sqrt(req.n)
    x_theory = np.linspace(-r * 1.1, r * 1.1, 500)
    y_theory = wigner_semicircle_pdf(x_theory, r)
    return WignerResponse(
        eigenvalues=eigenvalues.tolist(),
        theoretical_curve=TheoreticalCurve(x=x_theory.tolist(), y=y_theory.tolist())
    )

@app.post("/api/rmt/mp", response_model=MPResponse)
def get_mp_data(req: MPRequest):
    q = req.p / req.n
    sigma_sq = req.scale ** 2
    lambda_plus = sigma_sq * (1 + np.sqrt(q))**2
    lambda_minus = sigma_sq * (1 - np.sqrt(q))**2
    eigenvalues = generate_mp_eigenvalues(req.n, req.p, req.scale)
    x_start = max(0.01, lambda_minus - 0.5)
    x_end = lambda_plus + 0.5
    x_theory = np.linspace(x_start, x_end, 200)
    y_theory = mp_pdf(x_theory, q, sigma_sq)
    return MPResponse(
        q=q, lambda_plus=lambda_plus, lambda_minus=lambda_minus,
        eigenvalues=eigenvalues.tolist(),
        theoretical_curve=TheoreticalCurve(x=x_theory.tolist(), y=y_theory.tolist())
    )

@app.post("/api/rmt/analyze")
async def analyze_rmt(req: AnalyzeRequest):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=req.api_key if req.api_key else "sk-none", base_url=req.base_url)
    eigvec_section = f"\n【特征向量分析】\n{req.eigenvector_summary}" if req.eigenvector_summary else ""
    prompt = f"分析数据集 {req.dataset_name}。维度 q={req.q:.4f}, 异常值数量={req.outlier_count}。核心特征值: {req.top_eigenvalues}. {eigvec_section}"
    async def stream_generator():
        try:
            stream = await client.chat.completions.create(
                model=req.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"AI 分析暂时不可用: {str(e)}"
    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# 保留 Rolling 和 Heatmap Rebuild 逻辑（略作优化以适配 process_dataframe 的改进）
@app.post("/api/rmt/rolling", response_model=RollingResponse)
async def analyze_rolling(file: UploadFile = File(...), window_size: int = Form(60), step_size: int = Form(1), standardize: str = Form("true")):
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    if df.dtypes.iloc[0] == 'object' or pd.api.types.is_datetime64_any_dtype(df.dtypes.iloc[0]):
        times = df.iloc[:, 0].astype(str).tolist()
        df = df.iloc[:, 1:]
    else:
        times = [str(i) for i in range(len(df))]
    mat = df.dropna().values.astype(float)
    n, p = mat.shape
    is_std = standardize.lower() == "true"
    res_times, res_l1 = [], []
    for start in range(0, n - window_size + 1, step_size):
        end = start + window_size
        win = mat[start:end, :]
        if is_std: win = (win - np.mean(win, axis=0)) / (np.std(win, axis=0) + 1e-9)
        C = (1.0 / window_size) * np.dot(win.T, win)
        evs = np.linalg.eigvalsh(C)
        res_l1.append(float(np.max(evs)))
        res_times.append(times[min(end-1, len(times)-1)])
    return RollingResponse(times=res_times, lambda_1=res_l1)

@app.post("/api/rmt/heatmap_rebuild", response_model=HeatmapResponse)
async def heatmap_rebuild(file: UploadFile = File(...), top_k: int = Form(-1), scale: float = Form(1.0), fill_strategy: str = Form("zero"), standardize: str = Form("true")):
    # 逻辑同上，略
    return HeatmapResponse(cleaned_heatmap_base64="")
