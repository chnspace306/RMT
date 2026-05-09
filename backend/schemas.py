from pydantic import BaseModel, Field
from typing import List, Optional

class TopComponent(BaseModel):
    """异常特征值对应的特征向量中，权重最高的成分"""
    column_index: int = Field(description="原始矩阵中的列索引 (0-based)")
    column_name: str = Field(default="", description="列名/表头名称（若CSV有表头）")
    weight: float = Field(description="该列在特征向量中的权重(loading)")
    abs_weight: float = Field(description="权重的绝对值，用于排序")

class OutlierEigenvector(BaseModel):
    """一个异常特征值及其对应的高权重特征向量成分"""
    eigenvalue: float = Field(description="异常特征值的数值")
    rank: int = Field(description="在所有特征值中的排名 (1=最大)")
    top_components: List[TopComponent] = Field(description="权重绝对值最高的前N个成分")
    vector: List[float] = Field(description="完整的特征向量成分 (用于全景图表展示)", default_factory=list)

class AnalyzeRequest(BaseModel):
    dataset_name: str
    n: int
    p: int
    q: float
    sparsity: float
    lambda_plus: float
    lambda_minus: float
    top_eigenvalues: List[float]
    outlier_count: int
    model_name: str
    api_key: str
    base_url: str
    # 新增：异常特征值对应的高权重成分摘要（供AI分析使用）
    eigenvector_summary: str = ""

class WignerRequest(BaseModel):
    n: int = Field(default=1000, description="矩阵维度N")
    scale: float = Field(default=1.0, description="数值分布的缩放因子")

class TheoreticalCurve(BaseModel):
    x: List[float]
    y: List[float]

class WignerResponse(BaseModel):
    eigenvalues: List[float]
    theoretical_curve: TheoreticalCurve

class MPRequest(BaseModel):
    n: int = Field(default=1000, description="样本数 n")
    p: int = Field(default=350, description="特征数 p")
    scale: float = Field(default=1.0, description="分布的数值缩放因子")

class MPResponse(BaseModel):
    q: float
    lambda_plus: float
    lambda_minus: float
    eigenvalues: List[float]
    theoretical_curve: TheoreticalCurve
    sparsity: float = 0.0
    n: int = 0
    p: int = 0
    # 新增：异常特征值的特征向量高权重成分
    outlier_eigenvectors: List[OutlierEigenvector] = []
    column_names: List[str] = []
