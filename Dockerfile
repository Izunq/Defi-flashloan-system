# Frontend build stage
FROM node:18-alpine AS frontend-builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

# Frontend serve stage
FROM node:18-alpine AS frontend

WORKDIR /app

RUN npm install -g serve

COPY --from=frontend-builder /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
