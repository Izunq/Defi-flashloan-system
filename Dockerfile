# Dockerfile for Arbitrage Agent
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install snarkjs globally
RUN npm install -g snarkjs

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a directory for persistent data with proper permissions
RUN mkdir -p /data/agent_state && \
    chown -R appuser:appuser /data/agent_state && \
    chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CONFIG_FILE=/app/config_ultimate.yaml
ENV AGENT_STATE_DIR=/data/agent_state

# Expose port for potential API or dashboard
EXPOSE 8501

# Drop privileges to non-root user
USER appuser

# Set the entrypoint
ENTRYPOINT ["python", "python_agent_v34_ultimate.py"]

# Default command (can be overridden)
CMD ["--config", "/app/config_ultimate.yaml"]