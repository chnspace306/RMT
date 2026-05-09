from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import io

from backend.schemas import WignerRequest, WignerResponse, TheoreticalCurve, MPRequest, MPResponse, AnalyzeRequest, OutlierEigenvector, TopComponent, RollingResponse
from backend.rmt_core import generate_goe_eigenvalues, wigner_semicircle_pdf, generate_mp_eigenvalues, mp_pdf

app = FastAPI(title="RMT Backend API", version="1.0.0")

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/rmt/wigner", response_model=WignerResponse)
def get_wigner_data(req: WignerRequest):
    # 生成实际的高斯正交系 (GOE) 随机矩阵特征值
    eigenvalues = generate_goe_eigenvalues(req.n, req.scale)
    
    # Wigner 半圆律的理论半径 R = 2 * scale * sqrt(N)
    r = 2 * req.scale * np.sqrt(req.n)
    
    # 生成理论半圆律曲线用以在前端渲染
    x_theory = np.linspace(-r * 1.1, r * 1.1, 500)
    y_theory = wigner_semicircle_pdf(x_theory, r)
    
    return WignerResponse(
        eigenvalues=eigenvalues.tolist(),
        theoretical_curve=TheoreticalCurve(
            x=x_theory.tolist(),
            y=y_theory.tolist()
        )
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
        q=q,
        lambda_plus=lambda_plus,
        lambda_minus=lambda_minus,
        eigenvalues=eigenvalues.tolist(),
        theoretical_curve=TheoreticalCurve(
            x=x_theory.tolist(),
            y=y_theory.tolist()
        )
    )

@app.post("/api/rmt/upload", response_model=MPResponse)
async def upload_matrix(
    file: UploadFile = File(...), 
    scale: float = Form(...), 
    fill_strategy: str = Form("zero"),
    standardize: str = Form("true")
):
    contents = await file.read()
    text = contents.decode("utf-8")
    
    import warnings
    import csv as csv_mod
    
    # ====== 表头解析：尝试从 CSV 第一行中提取列名 ======
    lines = text.strip().split('\n')
    column_names: list[str] = []
    header_row = lines[0] if lines else ""
    # 启发式判断：如果第一行包含非数字内容，则视为表头
    try:
        first_cells = next(csv_mod.reader(io.StringIO(header_row)))
        has_header = False
        for cell in first_cells:
            cell_stripped = cell.strip()
            if cell_stripped and not cell_stripped.replace('.','',1).replace('-','',1).replace('e','',1).replace('E','',1).isdigit():
                has_header = True
                break
        if has_header:
            column_names = [c.strip() for c in first_cells]
    except Exception:
        pass
    
    mat = np.genfromtxt(io.StringIO(text), delimiter=',')
    if mat.ndim == 1:
        mat = mat.reshape(1, -1)
        
    mat = mat[~np.isnan(mat).all(axis=1)]
    if mat.size > 0:
        mat = mat[:, ~np.isnan(mat).all(axis=0)]
        
    if mat.size > 0:
        sparsity = 1.0 - (np.count_nonzero(np.nan_to_num(mat, nan=0.0)) / mat.size)
    else:
        sparsity = 0.0

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
    is_std = standardize.lower() == "true"
    
    eigenvectors = None
    if n > 1 and p > 0:
        if is_std:
            stds = np.std(mat, axis=0)
            stds[stds == 0] = 1.0  # Prevent divide by zero
            mat = (mat - np.mean(mat, axis=0)) / stds
            
        centered = mat - np.mean(mat, axis=0)
        C = (1.0 / n) * np.dot(centered.T, centered)  # Match exact MP limit scaling 1/N
        # 核心升级：使用 eigh 同时提取特征值和特征向量
        eigenvalues, eigenvectors = np.linalg.eigh(C)
    else:
        eigenvalues = np.array([])
        
    if is_std:
        sigma_sq = 1.0
    elif len(eigenvalues) > 0:
        sigma_sq = float(np.mean(eigenvalues))
    else:
        sigma_sq = scale ** 2
         
    lambda_plus = sigma_sq * (1 + np.sqrt(q))**2
    lambda_minus = sigma_sq * (1 - np.sqrt(q))**2
    
    # ====== 特征向量解析：提取异常特征值对应的高权重成分 ======
    outlier_eigenvectors: list[OutlierEigenvector] = []
    if eigenvectors is not None and len(eigenvalues) > 0:
        # eigh 返回的特征值是从小到大排列，特征向量按列对应
        sorted_indices = np.argsort(eigenvalues)[::-1]  # 从大到小
        
        rank = 0
        for idx in sorted_indices:
            ev = float(eigenvalues[idx])
            if ev <= lambda_plus:
                break  # 不再是异常值了
            rank += 1
            vec = eigenvectors[:, idx]  # 对应的特征向量
            abs_vec = np.abs(vec)
            # 取权重绝对值最高的前 5 个成分
            top_k = min(5, len(vec))
            top_indices = np.argsort(abs_vec)[::-1][:top_k]
            
            components = []
            for ci in top_indices:
                col_name = column_names[int(ci)] if int(ci) < len(column_names) else f"Column_{int(ci)}"
                components.append(TopComponent(
                    column_index=int(ci),
                    column_name=col_name,
                    weight=float(vec[ci]),
                    abs_weight=float(abs_vec[ci])
                ))
            
            outlier_eigenvectors.append(OutlierEigenvector(
                eigenvalue=ev,
                rank=rank,
                top_components=components,
                vector=[float(v) for v in vec]
            ))
            
            if rank >= 10:  # 最多展示前 10 个异常特征值的分解
                break
        
        # ====== IPR 计算与热力图渲染 ======
        try:
            ipr = np.sum(eigenvectors**4, axis=0).tolist()
        except:
            ipr = []
            
        cleaned_heatmap_base64 = None
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import base64
            
            signal_indices = np.where(eigenvalues > lambda_plus)[0]
            if len(signal_indices) > 0:
                C_clean = np.zeros_like(C)
                for idx in signal_indices:
                    v = eigenvectors[:, idx:idx+1]
                    C_clean += eigenvalues[idx] * np.dot(v, v.T)
                np.fill_diagonal(C_clean, 1.0)
            else:
                C_clean = C
            
            # 使用暗色背景渲染热力图以适配前端
            plt.style.use('dark_background')
            fig, axes = plt.subplots(1, 2, figsize=(10, 4), facecolor='#1c1c1e')
            
            im1 = axes[0].imshow(C, cmap='coolwarm', vmin=-1, vmax=1)
            axes[0].set_title('Original Correlation Matrix', color='white', pad=10)
            axes[0].axis('off')
            
            im2 = axes[1].imshow(C_clean, cmap='coolwarm', vmin=-1, vmax=1)
            axes[1].set_title('RMT Cleaned Heatmap', color='white', pad=10)
            axes[1].axis('off')
            
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=120, facecolor=fig.get_facecolor(), edgecolor='none')
            plt.close(fig)
            buf.seek(0)
            cleaned_heatmap_base64 = "data:image/png;base64," + base64.b64encode(buf.read()).decode('utf-8')
        except Exception as e:
            print("Heatmap Render Error:", e)
    else:
        ipr = []
        cleaned_heatmap_base64 = None
        
    x_start = max(0.01, lambda_minus - 0.5 * sigma_sq)
    x_end = lambda_plus + 0.5 * sigma_sq
    x_theory = np.linspace(x_start, x_end, 200)
    y_theory = mp_pdf(x_theory, q, sigma_sq)
    
    return MPResponse(
        q=q,
        lambda_plus=lambda_plus,
        lambda_minus=lambda_minus,
        eigenvalues=eigenvalues.tolist(),
        theoretical_curve=TheoreticalCurve(
            x=x_theory.tolist(),
            y=y_theory.tolist()
        ),
        sparsity=sparsity,
        n=n,
        p=p,
        outlier_eigenvectors=outlier_eigenvectors,
        column_names=column_names,
        ipr=ipr,
        cleaned_heatmap_base64=cleaned_heatmap_base64
    )

@app.post("/api/rmt/analyze")
async def analyze_rmt(req: AnalyzeRequest):
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(
        api_key=req.api_key if req.api_key else "sk-no-key-required",
        base_url=req.base_url
    )
    
    # 构建特征向量成分分析摘要
    eigvec_section = ""
    if req.eigenvector_summary:
        eigvec_section = f"""

【关键发现：异常特征值的特征向量成分解剖】
以下是每个异常特征值对应的特征向量中，权重（Loading）绝对值最高的核心列/变量。
这些变量是导致该特征值偏离随机噪声的「主导力量」，请基于这些成分的名称和符号来推断其物理/业务含义：
{req.eigenvector_summary}
"""
    
    prompt = f"""
作为一名顶尖的量化分析师和随机矩阵理论(RMT)专家，请对用户上传的数据集 '{req.dataset_name}' 的特征值谱密度进行专业解读。

【核心数据指标】
- 原矩阵维度: {req.n} 行(样本), {req.p} 列(特征)，维度比例 q = {req.q:.4f}
- 矩阵稀疏度: {req.sparsity * 100:.2f}% (值为0的元素比例)
- Marchenko-Pastur 理论噪音边界: [{req.lambda_minus:.4f}, {req.lambda_plus:.4f}]
- 真实特征值中，越过理论上限(代表真实信号)的数量: {req.outlier_count} 个
- 最大的几个核心特征值(头部的主成分): {', '.join(map(lambda x: f'{x:.4f}', req.top_eigenvalues))}
{eigvec_section}
【你的任务】
请直接输出一份专业、凝练、排版美观的 Markdown 简报（无需寒暄），深入浅出地解释：
1. 这个稀疏度和 q 值对数据结构的宏观影响。
2. 越过边界的这 {req.outlier_count} 个特征值（特别是最大的头部特征值）在现实中可能代表着什么。
   - 如果上方提供了「特征向量成分解剖」，请务必基于其中的列名/变量名，精确判断每个异常特征值代表的真实物理/业务事件（例如：该主成分由"贵州茅台、五粮液"主导 → 白酒板块共振效应）。
   - 注意特征向量权重的正负号：如果部分列为正、部分列为负，说明它们存在"跷跷板"对抗关系。
3. 数据集整体的「信噪比」结论（绝大部分特征值是否坍缩在 MP 理论边界内被视为噪音）。

注意：请直接输出 Markdown 文本，不要在最外层使用 ```markdown 代码块包裹！！！
"""
    
    async def stream_generator():
        try:
            stream = await client.chat.completions.create(
                model=req.model_name,
                messages=[
                    {"role": "system", "content": "你是一位专注于随机矩阵理论与复杂系统数据挖掘的资深科学家。请基于提供的特征向量成分精确分析每个异常特征值的物理/业务含义。"},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
                temperature=0.7
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\n\n**AI 忙碌中，请稍后再试...**\n\n💡 (内部异常: {str(e)})\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.post("/api/rmt/rolling", response_model=RollingResponse)
async def analyze_rolling(
    file: UploadFile = File(...), 
    window_size: int = Form(60),
    step_size: int = Form(1),
    standardize: str = Form("true")
):
    contents = await file.read()
    text = contents.decode("utf-8")
    
    import warnings
    mat = np.genfromtxt(io.StringIO(text), delimiter=',')
    mat = mat[~np.isnan(mat).all(axis=1)]
    if mat.ndim == 1:
        mat = mat.reshape(1, -1)
    
    mat = mat[~np.isnan(mat).any(axis=1)]
    n, p = mat.shape
    is_std = standardize.lower() == "true"
    
    times = []
    lambda_1_list = []
    
    for start in range(0, n - window_size + 1, step_size):
        end = start + window_size
        window_mat = mat[start:end, :]
        
        if is_std:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                stds = np.std(window_mat, axis=0)
                stds[stds == 0] = 1.0
                window_mat = (window_mat - np.mean(window_mat, axis=0)) / stds
        
        centered = window_mat - np.mean(window_mat, axis=0)
        C = (1.0 / window_size) * np.dot(centered.T, centered)
        
        try:
            eigenvalues, _ = np.linalg.eigh(C)
            if len(eigenvalues) > 0:
                lambda_1_list.append(float(np.max(eigenvalues)))
                times.append(str(end))
        except:
            pass
            
    return RollingResponse(times=times, lambda_1=lambda_1_list)
