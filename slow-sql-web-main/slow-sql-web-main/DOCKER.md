# Docker 部署指南

本文档介绍如何使用 Docker 构建和运行慢 SQL 分析系统。

## 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+（可选，用于使用 docker-compose）

## 快速开始

### 方式一：使用 Docker 命令

#### 1. 构建镜像

```bash
docker build -t slow-sql-analyzer:latest .
```

#### 2. 运行容器

```bash
docker run -d \
  --name slow-sql-web \
  -p 8080:80 \
  --restart unless-stopped \
  slow-sql-analyzer:latest
```

#### 3. 访问应用

打开浏览器访问：http://localhost:8080

### 方式二：使用 Docker Compose（推荐）

#### 1. 构建并启动

```bash
docker-compose up -d --build
```

#### 2. 查看日志

```bash
docker-compose logs -f
```

#### 3. 停止服务

```bash
docker-compose down
```

#### 4. 访问应用

打开浏览器访问：http://localhost:8080

## 环境变量配置

如果需要配置环境变量，可以通过以下方式：

### Docker 命令方式

```bash
docker run -d \
  --name slow-sql-web \
  -p 8080:80 \
  -e VITE_API_BASE_URL=http://your-api-server/api/v1 \
  slow-sql-analyzer:latest
```

### Docker Compose 方式

在 `docker-compose.yml` 中添加环境变量：

```yaml
services:
  slow-sql-web:
    environment:
      - VITE_API_BASE_URL=http://your-api-server/api/v1
```

**注意**：由于 Vite 在构建时会将环境变量打包进代码，如果需要修改环境变量，需要重新构建镜像。

## 构建时配置环境变量

如果需要构建时配置环境变量，可以使用 `--build-arg`：

```bash
docker build \
  --build-arg VITE_API_BASE_URL=http://your-api-server/api/v1 \
  -t slow-sql-analyzer:latest .
```

然后在 Dockerfile 中添加：

```dockerfile
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
```

## 镜像说明

### 多阶段构建

Dockerfile 使用多阶段构建，分为两个阶段：

1. **构建阶段** (`build-stage`)：
   - 基于 `node:20-alpine` 镜像
   - 安装 pnpm 包管理器
   - 安装项目依赖
   - 构建 React 应用（输出到 `dist` 目录）

2. **生产阶段** (`production-stage`)：
   - 基于 `nginx:alpine` 镜像
   - 复制构建产物到 Nginx 静态文件目录
   - 配置 Nginx 以支持 React Router

### 镜像大小优化

- 使用 Alpine Linux 基础镜像，减小镜像体积
- 多阶段构建，最终镜像只包含 Nginx 和静态文件
- 使用 `.dockerignore` 排除不必要的文件

## 常用命令

### 查看运行中的容器

```bash
docker ps
```

### 查看容器日志

```bash
docker logs -f slow-sql-web
```

### 进入容器

```bash
docker exec -it slow-sql-web sh
```

### 停止容器

```bash
docker stop slow-sql-web
```

### 删除容器

```bash
docker rm slow-sql-web
```

### 删除镜像

```bash
docker rmi slow-sql-analyzer:latest
```

## 故障排查

### 1. 端口被占用

如果 8080 端口被占用，可以修改端口映射：

```bash
docker run -d -p 3000:80 slow-sql-analyzer:latest
```

### 2. 构建失败

检查网络连接和 Docker 镜像源配置。

### 3. 页面刷新 404

确保 `nginx.conf` 已正确配置，包含 `try_files` 指令。

### 4. API 请求失败

检查环境变量 `VITE_API_BASE_URL` 是否正确配置，确保 API 服务器可访问。

## 生产环境建议

1. **使用 HTTPS**：配置 SSL 证书，使用 HTTPS 访问
2. **配置反向代理**：使用 Nginx 或 Traefik 作为反向代理
3. **监控和日志**：配置日志收集和监控系统
4. **资源限制**：设置容器资源限制（CPU、内存）
5. **健康检查**：添加健康检查配置

## 示例：生产环境 Docker Compose

```yaml
version: '3.8'

services:
  slow-sql-web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: slow-sql-analyzer-web
    ports:
      - "80:80"
      - "443:443"
    restart: always
    environment:
      - TZ=Asia/Shanghai
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - slow-sql-network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

networks:
  slow-sql-network:
    driver: bridge
```

