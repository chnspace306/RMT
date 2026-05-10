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

# 将 backend 文件夹的内容复制到 /app/backend/ 以保持 package 结构
# 这样 main.py 中的 from backend.schemas import ... 才能正常工作
COPY . ./backend/

# 暴露端口
EXPOSE 8000

# 启动命令
# 使用 ${PORT:-8000} 让 Zeabur 可以通过 PORT 环境变量指定端口
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
