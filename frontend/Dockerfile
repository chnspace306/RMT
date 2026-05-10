# 阶段 1: 构建
FROM node:18-alpine AS build-stage

WORKDIR /app

# 只要这两个文件没变，Docker 就会缓存依赖安装层，极大地加快后续部署速度
COPY package*.json ./

# 直接安装，不运行任何更新命令，避免环境冲突
RUN npm install

# 复制其余源码
COPY . .

# 注入环境变量（Vite 在构建时会将 VITE_ 开头的变量硬编码进 JS 文件）
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# 执行构建
RUN npm run build

# 阶段 2: 运行 (使用极简的 Nginx 镜像)
FROM nginx:stable-alpine AS production-stage

# 从构建阶段复制打包好的静态文件
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 暴露 Nginx 默认端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
