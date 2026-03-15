# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production || npm install --only=production

# Runtime stage
FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache dumb-init

COPY --from=builder /app/node_modules ./node_modules
COPY . .

EXPOSE 3001

ENTRYPOINT ["dumb-init", "--"]
CMD ["npm", "start"]
