# Frontend Docker 说明

当前项目默认不再单独部署前端容器，也不再以子目录 `docker-compose.yml` 作为入口。

前端镜像由仓库根目录 `docker-compose.local.yml` 统一构建和启动，并通过容器内 Nginx 把 `/api/*` 反向代理到后端容器，因此默认不需要在前端镜像里写死 `VITE_API_BASE_URL`。

推荐入口：

```bash
cd ../../
docker compose -f docker-compose.local.yml up -d --build
```

默认访问地址：

- 前端：`http://127.0.0.1:3000`
- 后端：`http://127.0.0.1:10800/docs`

仅当你明确要绕过容器内代理、让前端直连其他后端地址时，才需要在构建时传入：

```bash
docker build \
  --build-arg VITE_API_BASE_URL=http://your-api-server \
  -t slow-sql-analyzer:latest .
```

但对于当前仓库的默认本地联调路径，这不是必需项。
