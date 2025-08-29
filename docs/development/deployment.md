# Deployment Guide

This guide covers various deployment options for Bio Hit Finder, from local development to production cloud deployments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Platforms](#cloud-platforms)
4. [Production Considerations](#production-considerations)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

## Local Development

### Development Server

For local development and testing:

```bash
# Standard development server
streamlit run app.py

# With custom configuration
streamlit run app.py --server.port 8502 --server.address 0.0.0.0

# With debugging enabled
export STREAMLIT_LOGGER_LEVEL=debug
streamlit run app.py --logger.level debug
```

### Configuration Options

Create `.streamlit/config.toml` for local configuration:

```toml
[server]
port = 8501
address = "0.0.0.0"
maxUploadSize = 1000
maxMessageSize = 1000
enableXsrfProtection = true
enableCORS = false

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[logger]
level = "info"
messageFormat = "%(asctime)s %(message)s"
```

### Environment Variables

Set environment variables for configuration:

```bash
# .env file
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
BIO_HIT_FINDER_LOG_LEVEL=INFO
BIO_HIT_FINDER_MAX_FILE_SIZE=100MB
```

## Docker Deployment

### Basic Docker Setup

#### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Build and Run

```bash
# Build image
docker build -t bio-hit-finder:latest .

# Run container
docker run -d \
  --name bio-hit-finder \
  -p 8501:8501 \
  -e STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
  -e STREAMLIT_SERVER_PORT=8501 \
  bio-hit-finder:latest

# View logs
docker logs bio-hit-finder

# Stop container
docker stop bio-hit-finder
```

### Production Docker Setup

#### Multi-stage Dockerfile

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Add local packages to PATH
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  bio-hit-finder:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    volumes:
      - ./data:/app/data:ro
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - bio-hit-finder
    restart: unless-stopped
```

#### Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream bio_hit_finder {
        server bio-hit-finder:8501;
    }

    server {
        listen 80;
        server_name your-domain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Increase upload size for large data files
        client_max_body_size 1000M;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;

        location / {
            proxy_pass http://bio_hit_finder;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support for Streamlit
        location /_stcore/stream {
            proxy_pass http://bio_hit_finder;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
```

## Cloud Platforms

### Streamlit Cloud

#### Setup

1. **Fork repository** to your GitHub account
2. **Connect to Streamlit Cloud**:
   - Visit https://share.streamlit.io/
   - Connect your GitHub account
   - Select your repository

3. **Configure deployment**:
   ```toml
   # .streamlit/config.toml
   [server]
   maxUploadSize = 1000
   
   [theme]
   primaryColor = "#1f77b4"
   ```

4. **Add requirements**:
   ```txt
   # requirements.txt (Streamlit Cloud specific)
   streamlit>=1.28.0
   pandas>=2.0.0
   numpy>=1.24.0
   plotly>=5.15.0
   scipy>=1.11.0
   openpyxl>=3.1.0
   jinja2>=3.1.0
   weasyprint>=59.0
   ```

#### Streamlit Cloud Secrets

```toml
# .streamlit/secrets.toml (not committed to repo)
[general]
api_key = "your-api-key"
max_file_size = 1000000000

[database]
host = "your-db-host"
username = "your-username"
password = "your-password"
```

### AWS Deployment

#### ECS with Fargate

```yaml
# ecs-task-definition.json
{
  "family": "bio-hit-finder",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "bio-hit-finder",
      "image": "your-account.dkr.ecr.region.amazonaws.com/bio-hit-finder:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "STREAMLIT_SERVER_ADDRESS",
          "value": "0.0.0.0"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/bio-hit-finder",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Application Load Balancer

```yaml
# ALB configuration
Resources:
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Type: application
      Scheme: internet-facing
      SecurityGroups: [!Ref ALBSecurityGroup]
      Subnets: [!Ref PublicSubnet1, !Ref PublicSubnet2]

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Port: 8501
      Protocol: HTTP
      VpcId: !Ref VPC
      TargetType: ip
      HealthCheckPath: /_stcore/health
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 10
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT_ID/bio-hit-finder

gcloud run deploy bio-hit-finder \
  --image gcr.io/PROJECT_ID/bio-hit-finder \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10
```

#### Cloud Run Configuration

```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: bio-hit-finder
  labels:
    cloud.googleapis.com/location: us-central1
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/memory: "4Gi"
        run.googleapis.com/cpu: "2"
        run.googleapis.com/timeout: "3600s"
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/bio-hit-finder
        ports:
        - containerPort: 8501
        env:
        - name: STREAMLIT_SERVER_ADDRESS
          value: "0.0.0.0"
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
```

### Azure Deployment

#### Container Instances

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group bio-hit-finder-rg \
  --name bio-hit-finder \
  --image your-registry.azurecr.io/bio-hit-finder:latest \
  --dns-name-label bio-hit-finder-unique \
  --ports 8501 \
  --memory 4 \
  --cpu 2 \
  --environment-variables STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

#### App Service

```yaml
# azure-pipelines.yml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  dockerRegistryServiceConnection: 'your-acr-connection'
  imageRepository: 'bio-hit-finder'
  containerRegistry: 'your-registry.azurecr.io'
  dockerfilePath: '$(Build.SourcesDirectory)/Dockerfile'
  tag: '$(Build.BuildId)'

stages:
- stage: Build
  displayName: Build and push stage
  jobs:
  - job: Build
    displayName: Build
    steps:
    - task: Docker@2
      displayName: Build and push image
      inputs:
        command: buildAndPush
        repository: $(imageRepository)
        dockerfile: $(dockerfilePath)
        containerRegistry: $(dockerRegistryServiceConnection)
        tags: |
          $(tag)
          latest
```

## Production Considerations

### Security

#### HTTPS Configuration

```bash
# Let's Encrypt SSL certificate
certbot --nginx -d your-domain.com

# Or use custom certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem -out cert.pem
```

#### Authentication

```python
# Simple authentication (for demonstration)
import streamlit as st
import hashlib

def check_password():
    """Returns True if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    # Your app content here
    st.write("Welcome to Bio Hit Finder!")
```

### Performance Optimization

#### Configuration

```toml
# .streamlit/config.toml - Production settings
[server]
maxUploadSize = 1000
maxMessageSize = 1000
enableCORS = false
enableXsrfProtection = true

[runner]
magicEnabled = false
fastReruns = true

[browser]
gatherUsageStats = false
```

#### Caching Strategy

```python
# Enhanced caching for production
import streamlit as st
from functools import lru_cache

@st.cache_data(ttl=3600, max_entries=100)
def load_and_process_data(file_hash: str, config_hash: str):
    """Cache processed data with TTL and size limits."""
    pass

@st.cache_resource
def load_processor():
    """Cache expensive resources."""
    return PlateProcessor()

# Memory-efficient processing
@lru_cache(maxsize=50)
def calculate_statistics(data_tuple):
    """LRU cache for expensive calculations."""
    pass
```

### Resource Management

#### Memory Limits

```python
# Memory monitoring
import psutil
import streamlit as st

def check_memory_usage():
    """Monitor memory usage and warn if high."""
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 80:
        st.warning(f"High memory usage: {memory_percent}%")
    return memory_percent

# Resource cleanup
def cleanup_temp_files():
    """Clean up temporary files."""
    import tempfile
    import shutil
    
    temp_dir = tempfile.gettempdir()
    # Clean up old temporary files
```

#### CPU Optimization

```python
# Multi-processing configuration
import multiprocessing

def get_optimal_workers():
    """Determine optimal number of workers."""
    cpu_count = multiprocessing.cpu_count()
    # Use n-1 cores to leave one for system
    return max(1, cpu_count - 1)
```

## Monitoring & Maintenance

### Health Checks

```python
# health_check.py
import requests
import sys
import time

def check_application_health(url="http://localhost:8501"):
    """Check if application is healthy."""
    try:
        # Check main health endpoint
        response = requests.get(f"{url}/_stcore/health", timeout=10)
        if response.status_code != 200:
            return False
        
        # Check if main page loads
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return False
        
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    if not check_application_health():
        sys.exit(1)
```

### Logging Configuration

```python
# logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure logging for production."""
    
    # Create logger
    logger = logging.getLogger('bio_hit_finder')
    logger.setLevel(logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/bio_hit_finder.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger
```

### Metrics Collection

```python
# metrics.py
import time
from functools import wraps
from collections import defaultdict

class MetricsCollector:
    """Simple metrics collector for production monitoring."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
    
    def time_function(self, func_name):
        """Decorator to time function execution."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    self.counters[f"{func_name}_success"] += 1
                    return result
                except Exception as e:
                    self.counters[f"{func_name}_error"] += 1
                    raise
                finally:
                    execution_time = time.time() - start_time
                    self.metrics[f"{func_name}_time"].append(execution_time)
            return wrapper
        return decorator
    
    def get_metrics(self):
        """Return collected metrics."""
        return {
            'execution_times': dict(self.metrics),
            'counters': dict(self.counters)
        }

# Usage
metrics = MetricsCollector()

@metrics.time_function("data_processing")
def process_data():
    # Your processing code here
    pass
```

## Troubleshooting

### Common Issues

#### Memory Issues

```bash
# Check memory usage
docker stats bio-hit-finder

# Increase memory limit
docker run -m 4g bio-hit-finder:latest
```

#### Port Conflicts

```bash
# Find process using port
lsof -i :8501
netstat -tulpn | grep :8501

# Kill process
kill -9 <PID>
```

#### SSL Certificate Issues

```bash
# Check certificate expiry
openssl x509 -in cert.pem -text -noout | grep "Not After"

# Renew Let's Encrypt certificate
certbot renew --nginx
```

#### Performance Issues

```python
# Profile application
import cProfile
import pstats

def profile_function():
    """Profile a specific function."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your code here
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(10)
```

### Log Analysis

```bash
# View recent logs
docker logs -f bio-hit-finder

# Search for errors
docker logs bio-hit-finder 2>&1 | grep -i error

# Monitor resource usage
docker exec bio-hit-finder ps aux
```

### Backup and Recovery

```bash
# Backup data directory
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# Database backup (if applicable)
pg_dump bio_hit_finder > backup.sql

# Restore from backup
tar -xzf backup_20240115.tar.gz
```

---

This deployment guide provides comprehensive coverage of various deployment scenarios. Choose the option that best fits your infrastructure requirements and security needs.