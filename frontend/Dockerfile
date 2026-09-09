FROM node:22-bookworm-slim

WORKDIR /app

COPY package.json package-lock.json ./
# Prefetch with: docker run --rm -v "$PWD":/app -v "$PWD/../.npm-cache":/root/.npm -w /app node:22-bookworm-slim npm ci --no-audit --no-fund
COPY node_modules ./node_modules
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
