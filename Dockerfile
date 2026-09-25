FROM node:20-alpine

WORKDIR /app

# Copy package definitions first for optimal caching
COPY package.json ./

# Install only production dependencies cleanly
RUN npm install --omit=dev --no-package-lock

# Copy application source code and protocol definitions
COPY server.js ./
COPY src/ ./src/
COPY proto/ ./proto/

# Expose REST and gRPC ports
EXPOSE 8080
EXPOSE 50051

ENV PORT=8080
ENV GRPC_PORT=50051
ENV REDIS_URL=redis://redis:6379

CMD ["node", "server.js"]
