FROM python:3.12-slim

WORKDIR /app

# 安装必要的系统库（Matplotlib 渲染需要）
RUN apt-get update && apt-get install -y \
    build-essential \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制并安装依赖（利用 Docker 缓存层加速重建）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 将代码和数据集复制到镜像中
COPY . ./backend/
COPY Datasets/ ./backend/Datasets/

# 暴露端口 (与 Zeabur 截图中的 8080 保持一致)
EXPOSE 8080

# 启动命令
# 使用 ${PORT:-8080} 确保即使环境变量失效，也默认运行在 8080 端口
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
