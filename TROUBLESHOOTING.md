# Troubleshooting Guide

## Docker Build Issues

### Package Installation Errors

If you encounter errors like:
```
failed to solve: process "/bin/sh -c apt-get update && apt-get install -y ..." did not complete successfully: exit code: 100
```

**Solution 1: Use the Simple Dockerfile**
```bash
# Use the simple Dockerfile that minimizes system dependencies
docker build -f Dockerfile.simple -t book-scraper:latest .
```

**Solution 2: Use the Alternative Dockerfile**
```bash
# Use the alternative Dockerfile with better compatibility
docker build -f Dockerfile.alternative -t book-scraper:latest .
```

**Solution 3: Fix Package Names**
The issue is often with package names. For Python 3.11-slim:
- `libffi7` → `libffi8` (or remove if not needed)
- `libssl3` → `libssl1.1` (for older base images)

### Memory Issues During Build

If the build fails due to memory constraints:
```bash
# Increase Docker memory limit
# In Docker Desktop: Settings → Resources → Memory → Increase to 4GB+

# Or use buildkit with memory limits
DOCKER_BUILDKIT=1 docker build --memory=4g -t book-scraper:latest .
```

## Runtime Issues

### Import Errors

If you get import errors like:
```
ModuleNotFoundError: No module named 'lxml'
```

**Solution:**
```bash
# Rebuild with the correct Dockerfile
docker build -f Dockerfile.simple -t book-scraper:latest .

# Or install missing packages manually
docker exec -it <container_name> pip install lxml
```

### Permission Errors

If you get permission errors:
```bash
# Check if the container is running as the correct user
docker exec -it <container_name> whoami

# Should show: appuser
```

## Docker Compose Issues

### Service Won't Start

```bash
# Check logs
docker-compose logs book-scraper

# Restart services
docker-compose down
docker-compose up --build

# Check if ports are available
netstat -tulpn | grep :8000
```

### Redis Connection Issues

```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Should return: PONG

# Check Redis logs
docker-compose logs redis
```

## Kubernetes Issues

### Pod Won't Start

```bash
# Check pod status
kubectl get pods -n book-scraper

# Check pod events
kubectl describe pod <pod-name> -n book-scraper

# Check logs
kubectl logs <pod-name> -n book-scraper
```

### Image Pull Errors

```bash
# Check if image exists
docker images | grep book-scraper

# Push image to registry
docker tag book-scraper:latest gcr.io/<project-id>/book-scraper:latest
docker push gcr.io/<project-id>/book-scraper:latest
```

## Performance Issues

### High Memory Usage

```bash
# Check container resource usage
docker stats

# Adjust memory limits in docker-compose.yml
services:
  book-scraper:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Slow Scraping

```bash
# Check rate limiting settings
curl http://localhost:8000/api/v1/stats

# Adjust rate limits in environment variables
MAX_CONCURRENT_REQUESTS=200
RATE_LIMIT_PER_SECOND=20
```

## Common Solutions

### 1. Clean Docker Environment
```bash
# Remove all containers and images
docker system prune -a

# Remove volumes
docker volume prune

# Rebuild from scratch
docker-compose up --build
```

### 2. Check Dependencies
```bash
# Verify Python packages
docker exec -it <container_name> pip list

# Check system packages
docker exec -it <container_name> dpkg -l | grep -E "(libxml|libxslt|libffi|libssl)"
```

### 3. Use Different Base Image
```bash
# Try different Python base images
FROM python:3.11-bullseye  # More stable, larger
FROM python:3.11-slim      # Smaller, may have dependency issues
FROM python:3.11-alpine    # Smallest, different package manager
```

### 4. Debug Container
```bash
# Run interactive shell
docker run -it --rm book-scraper:latest /bin/bash

# Check what's available
ls -la /usr/lib/x86_64-linux-gnu/ | grep -E "(libxml|libxslt|libffi|libssl)"
```

## Environment-Specific Issues

### macOS
- Docker Desktop memory limits
- File sharing permissions
- Port conflicts

### Linux
- SELinux policies
- AppArmor profiles
- System package conflicts

### Windows
- WSL2 memory limits
- File path issues
- Docker Desktop settings

## Getting Help

1. **Check logs first**: `docker-compose logs` or `kubectl logs`
2. **Verify configuration**: Check environment variables and config files
3. **Test locally**: Try running the Python app directly without Docker
4. **Check dependencies**: Ensure all required packages are available
5. **Use simple Dockerfile**: Start with `Dockerfile.simple` and add complexity gradually

## Quick Fix Commands

```bash
# Most common fixes
docker-compose down
docker system prune -f
docker-compose up --build

# If still having issues
docker build -f Dockerfile.simple -t book-scraper:latest .
docker run -p 8000:8000 book-scraper:latest
``` 