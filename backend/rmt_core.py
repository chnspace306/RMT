import numpy as np
import scipy

def generate_goe_eigenvalues(n: int, scale: float = 1.0) -> np.ndarray:
    """
    生成维度为 N x N 的高斯正交系 (GOE) 随机矩阵的特征值。
    """
    # 生成随机正态分布矩阵，非对角元方差为 scale^2，这里先生成后对称化
    A = np.random.normal(loc=0.0, scale=scale, size=(n, n))
    
    # 对称化 A 以得到 GOE 矩阵 H
    # (A + A.T) / sqrt(2) 保持了非对角线方差为 scale^2
    H = (A + A.T) / np.sqrt(2.0)
    
    # 求解特征值
    eigenvalues = np.linalg.eigvalsh(H)
    return eigenvalues

def wigner_semicircle_pdf(x: np.ndarray, r: float) -> np.ndarray:
    """
    计算给定特征值数组 x 和半径 R 下的 Wigner 半圆律理论概率密度值。
    """
    y = np.zeros_like(x, dtype=float)
    mask = np.abs(x) <= r
    # 半圆律公式
    y[mask] = (2.0 / (np.pi * r**2)) * np.sqrt(r**2 - x[mask]**2)
    return y

def generate_mp_eigenvalues(n: int, p: int, scale: float = 1.0) -> np.ndarray:
    """
    生成维度为 n x p 的正态分布随机矩阵 X，计算样本协方差矩阵 C = (1/n) * X.T * X，
    并使用 np.linalg.eigvalsh 返回其所有特征值的列表。
    """
    X = np.random.normal(loc=0.0, scale=scale, size=(n, p))
    C = (1.0 / n) * np.dot(X.T, X)
    eigenvalues = np.linalg.eigvalsh(C)
    return eigenvalues

def mp_pdf(x: np.ndarray, q: float, sigma_sq: float = 1.0) -> np.ndarray:
    """
    根据 MP 分布理论公式计算概率密度。
    若 x 超出理论上下界 [sigma^2(1-sqrt(q))^2, sigma^2(1+sqrt(q))^2]，则返回 0.0。
    """
    lambda_plus = sigma_sq * (1 + np.sqrt(q))**2
    lambda_minus = sigma_sq * (1 - np.sqrt(q))**2
    
    y = np.zeros_like(x, dtype=float)
    mask = (x >= lambda_minus) & (x <= lambda_plus) & (x > 0)
    
    val = (lambda_plus - x[mask]) * (x[mask] - lambda_minus)
    val = np.maximum(val, 0.0)
    
    y[mask] = np.sqrt(val) / (2 * np.pi * q * x[mask] * sigma_sq)
    return y
