# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm cache clean --force && npm install
COPY . .
RUN npm run build

# Production stage with Caddy
FROM caddy:alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY start.sh /start.sh
COPY --from=build /app/build /app/build
RUN chmod +x /start.sh
EXPOSE 3000
CMD ["sh", "/start.sh"]