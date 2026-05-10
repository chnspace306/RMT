# 阶段 1: 构建
FROM node:18-slim AS build-stage

WORKDIR /app

# 复制 package.json 并安装依赖
COPY package*.json ./
RUN npm install

# 复制源代码并打包
COPY . .
# 注入环境变量（虽然 Vercel 会注入，但 Docker 模式下需要显式处理或让 Vite 读取 .env）
RUN npm run build

# 阶段 2: 运行
FROM nginx:stable-alpine AS production-stage

# 复制打包后的文件到 Nginx 目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 暴露 80 端口（Nginx 默认）
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
