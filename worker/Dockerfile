FROM gcc:latest AS builder
WORKDIR /app
COPY engine.c .
RUN gcc -O3 -mavx2 engine.c -o engine

FROM node:18-slim
WORKDIR /app
COPY package*.json ./
RUN npm install --only=production
COPY --from=builder /app/engine .
COPY server.js .

EXPOSE 8080
CMD ["node", "server.js"]
