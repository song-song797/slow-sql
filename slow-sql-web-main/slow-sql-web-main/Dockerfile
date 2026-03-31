# 构建 React 项目
FROM reg.un-net.com/node/node:20-alpine AS build-stage

# 1. 定义构建参数（接收后端地址，默认值可选）
ARG VITE_API_BASE_URL  # Vite用，CRA则改为ARG REACT_APP_API_BASE_URL

# 2. 将构建参数设置为容器内的环境变量
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL 

RUN npm config set registry https://registry.npmmirror.com

# 安装 pnpm
RUN npm install -g pnpm

RUN pnpm config set registry https://registry.npmmirror.com

WORKDIR /app

# 复制依赖文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖（使用 pnpm）
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 构建项目（Vite 默认输出到 dist 目录）
RUN pnpm run build

# 替换为企业私有Nginx镜像
FROM reg.un-net.com/nginx/nginx:latest AS production-stage

# 复制第一阶段构建的静态文件到 Nginx 的默认静态文件目录
# Vite 构建输出在 dist 目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制 Nginx 配置文件（解决 React 路由刷新 404 问题）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 10801

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]       