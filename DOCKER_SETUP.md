# Docker Setup Guide

## Quick Start (Development)

```bash
# Copy environment variables
cp .env.example .env

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- Proxy Server: http://localhost:3001
- MongoDB: localhost:27017
- Redis: localhost:6379

## Development with Hot Reload

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

This enables file watching and automatic reloads for:
- Frontend (Vite dev server on port 5173)
- Backend (source files)
- Server proxy (source files)

## Environment Variables

Required in `.env`:
```
INFURA_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
EXECUTOR_PRIVATE_KEY=0xYOUR_PRIVATE_KEY
ARBITRAGE_CONTRACT_ADDRESS=0xYOUR_CONTRACT_ADDRESS
MONGO_PASSWORD=your_secure_password
```

## Container Details

### Frontend (React + Vite)
- **Image**: new_flashloan-frontend:latest
- **Port**: 3000
- **Dev Port**: 5173 (when using docker-compose.dev.yml)
- **Build**: Multi-stage (build → serve with Node.js)

### Backend (Node.js + Express)
- **Image**: new_flashloan-backend:latest
- **Port**: 8080
- **Database**: MongoDB
- **Cache**: Redis
- **Process Manager**: dumb-init (proper signal handling)

### Server Proxy (Node.js + Express)
- **Image**: new_flashloan-proxy:latest
- **Port**: 3001
- **Features**: Rate limiting, CORS, request proxying

### MongoDB
- **Image**: mongo:7-alpine
- **Port**: 27017
- **Data Volume**: mongo-data
- **Auth**: Configured with admin user

### Redis
- **Image**: redis:7-alpine
- **Port**: 6379
- **Data Volume**: redis-data
- **Options**: AOF persistence enabled

## Common Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Rebuild images after changes
docker compose build --no-cache

# View specific service logs
docker compose logs backend
docker compose logs -f frontend

# Execute command in running container
docker compose exec backend npm audit
docker compose exec mongo mongosh

# Remove volumes (careful - data loss)
docker compose down -v

# Restart a service
docker compose restart backend
```

## Troubleshooting

**Port already in use:**
```bash
# Change ports in docker-compose.yml or use -p flag
docker compose -p myproject up -d
```

**Container keeps restarting:**
```bash
docker compose logs backend  # Check error messages
```

**MongoDB connection failed:**
```bash
# Ensure MongoDB is running
docker compose ps
# Check credentials in .env
```

**Clear everything and start fresh:**
```bash
docker compose down -v
docker system prune -a
docker compose up -d
```

## Production Considerations

For production deployment:

1. Use specific image versions (not `latest`)
2. Set resource limits in docker-compose.yml
3. Configure proper logging
4. Use secrets management (not .env file)
5. Enable HTTPS/TLS
6. Set up monitoring and health checks
7. Consider using Docker Swarm or Kubernetes

Example resource limits:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Performance Tips

- Alpine-based images reduce size (~230MB backend, ~195MB server)
- Multi-stage builds exclude dev dependencies
- dumb-init ensures proper signal handling for graceful shutdowns
- Bind mounts for development enable live code reloading
- Docker layer caching optimizes rebuild times

## Image Sizes

- Backend: 230MB (includes Node.js + dependencies)
- Server Proxy: 195MB (includes Node.js + dependencies)
- Frontend: ~500MB (build stage includes TypeScript compiler)

## Cleanup

```bash
# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Full cleanup (careful!)
docker system prune -a
```
