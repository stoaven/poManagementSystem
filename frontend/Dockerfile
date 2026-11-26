# 前端镜像：构建静态资源 → nginx 托管
# 前端用的是 hash 路由（/#/shipments/6），API 走同源的 /api/v1，
# 所以构建时不需要注入任何环境变量，nginx 反代到 backend 服务即可。
FROM node:20-alpine AS build

WORKDIR /app

# 依赖单独一层：只改业务代码时不必重装依赖
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
