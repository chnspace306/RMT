FROM python:3.12-slim

WORKDIR /app

# 安装必要的系统库（Matplotlib 渲染可能需要）
RUN apt-get update && apt-get install -y \
    build-essential \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口（Zeabur/Render/Railway 会自动识别）
EXPOSE 8000

# 启动命令
# 使用 backend.main:app 是因为项目结构中 main.py 在 backend 文件夹下
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
