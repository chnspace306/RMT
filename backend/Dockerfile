FROM python:3.12-slim

WORKDIR /app

# 安装必要的系统库
RUN apt-get update && apt-get install -y \
    build-essential \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 将 backend 文件夹的内容复制到 /app/backend/ 以保持 package 结构
COPY . ./backend/

# 暴露端口
EXPOSE 8000

# 启动命令 - 保持 backend.main:app 的包路径
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
