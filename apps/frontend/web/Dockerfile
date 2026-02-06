FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
ENV PORT=8080
ENV API_URL=https://generalrag-api-dev-668754198632.us-central1.run.app
EXPOSE 8080
CMD ["node", "server.js"]
