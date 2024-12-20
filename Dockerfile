# Multi-stage build for Vocality Nexus

# Backend Stage
FROM python:3.9-slim AS backend-build
WORKDIR /app/backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/backend/ .

# Frontend Stage
FROM node:16-alpine AS frontend-build
WORKDIR /app/frontend
COPY package*.json ./
RUN npm ci
COPY src/frontend/ .
RUN npm run build

# Final Stage
FROM python:3.9-slim
WORKDIR /app

# Copy backend artifacts
COPY --from=backend-build /app/backend /app/backend
COPY --from=backend-build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy frontend artifacts
COPY --from=frontend-build /app/frontend/build /app/frontend/build

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 5000

# Set environment variables
ENV FLASK_APP=src/backend/app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the application
CMD ["flask", "run"]
