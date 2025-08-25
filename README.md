# Book Scraper Backend Service

A high-performance, scalable book scraping service designed for Kubernetes deployment on Google Kubernetes Engine (GKE). Built with Python, FastAPI, and async/await architecture for maximum performance.

## 🚀 Features

- **High-Performance Async Scraping**: Built with asyncio and httpx for maximum concurrency
- **Intelligent Rate Limiting**: Per-domain rate limiting with adaptive algorithms
- **Multiple HTML Parsers**: Fallback parsing with BeautifulSoup, Selectolax, and lxml
- **Kubernetes Ready**: Full K8s deployment with HPA, health checks, and monitoring
- **Prometheus Metrics**: Comprehensive metrics collection for observability
- **Multi-Source Support**: Goodreads, Amazon, Google Books, OpenLibrary
- **Robust Error Handling**: Retry logic, circuit breakers, and graceful degradation
- **Production Ready**: Health checks, readiness probes, and security best practices

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  ScraperEngine  │    │   HTTP Client   │
│                 │    │                 │    │                 │
│ - REST API      │◄──►│ - Task Queue    │◄──►│ - Connection    │
│ - Health Checks │    │ - Rate Limiting │    │   Pooling       │
│ - Metrics       │    │ - Concurrency   │    │ - Retry Logic   │
└─────────────────┘    │   Control       │    └─────────────────┘
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  HTML Parser    │
                       │                 │
                       │ - Multiple      │
                       │   Engines       │
                       │ - Structured    │
                       │   Data          │
                       └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **HTTP Client**: httpx, aiohttp with connection pooling
- **HTML Parsing**: BeautifulSoup4, Selectolax, lxml
- **Task Queue**: Redis, Celery (optional)
- **Database**: Abstracted layer (PostgreSQL, MongoDB ready)
- **Monitoring**: Prometheus, Grafana
- **Containerization**: Docker, multi-stage builds
- **Orchestration**: Kubernetes, GKE
- **CI/CD**: Ready for Cloud Build, GitHub Actions

## 📦 Installation

### Prerequisites

- Python 3.11+
- Docker
- Kubernetes cluster (GKE, minikube, etc.)
- Redis (for production)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd book-scraper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run with Docker Compose**

   **Option A: Core services only (recommended for development)**
   ```bash
   docker-compose -f docker-compose.core.yml up --build
   ```

   **Option B: Full stack with monitoring**
   ```bash
   docker-compose --profile monitoring up --build
   ```

   **Option C: All services**
   ```bash
   docker-compose up --build
   ```

5. **Access the service**
   - API: http://localhost:8000
   - Metrics: http://localhost:9090
   - Redis: localhost:6379
   - Prometheus: http://localhost:9091 (if monitoring enabled)
   - Grafana: http://localhost:3000 (admin/admin, if monitoring enabled)

### Production Deployment

1. **Build Docker image**
   ```bash
   # Use the simple Dockerfile to avoid dependency issues
   docker build -f Dockerfile.simple -t book-scraper:latest .
   
   # Or use the alternative for better compatibility
   docker build -f Dockerfile.alternative -t book-scraper:latest .
   ```

2. **Deploy to GKE**
   ```bash
   # Update PROJECT_ID in deploy.sh
   chmod +x deploy.sh
   ./deploy.sh
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | HTTP port |
| `WORKERS` | `4` | Number of worker processes |
| `MAX_CONCURRENT_REQUESTS` | `100` | Max concurrent HTTP requests |
| `RATE_LIMIT_PER_SECOND` | `10` | Global rate limit |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
| `ENABLE_METRICS` | `true` | Enable Prometheus metrics |

### Rate Limiting Configuration

The service includes intelligent rate limiting per domain:

- **Goodreads**: 2 req/s (conservative)
- **Amazon**: 1 req/s (very conservative)
- **Google Books**: 5 req/s (permissive)
- **OpenLibrary**: 8 req/s (permissive)

## 📊 API Endpoints

### Core Endpoints

- `GET /` - Service information
- `GET /health` - Health check (Kubernetes)
- `GET /ready` - Readiness check (Kubernetes)
- `GET /metrics` - Prometheus metrics
- `GET /info` - Service configuration

### Scraping API

- `POST /api/v1/scrape` - Batch scrape books
- `POST /api/v1/scrape/single` - Scrape single book
- `GET /api/v1/results` - Get scraping results
- `GET /api/v1/stats` - Get scraper statistics
- `DELETE /api/v1/results` - Clear results

### Example Usage

```bash
# Scrape a single book
curl -X POST "http://localhost:8000/api/v1/scrape/single" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone",
    "source": "goodreads",
    "priority": 5
  }'

# Batch scrape
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone",
      "https://www.goodreads.com/book/show/5.Harry_Potter_and_the_Prisoner_of_Azkaban"
    ],
    "source": "goodreads",
    "priority": 3
  }'
```

### API Request Models

**Single Book Scraping:**
```json
{
  "url": "https://example.com/book/123",
  "source": "goodreads",
  "priority": 5
}
```

**Batch Scraping:**
```json
{
  "urls": [
    "https://example.com/book/123",
    "https://example.com/book/456"
  ],
  "source": "goodreads",
  "priority": 3,
  "metadata": {
    "batch_id": "batch_001",
    "user_id": "user_123"
  }
}
```

## 🚀 Performance Features

### Async Architecture
- **Concurrent Processing**: Up to 100 concurrent requests
- **Connection Pooling**: HTTP/2 support with keep-alive
- **Non-blocking I/O**: Full async/await implementation

### Rate Limiting
- **Token Bucket Algorithm**: Efficient rate limiting
- **Per-Domain Limits**: Different limits per source
- **Adaptive Limiting**: Adjusts based on response patterns
- **Jitter**: Random delays to avoid detection

### HTML Parsing
- **Multiple Engines**: Fallback parsing for reliability
- **Structured Data**: JSON-LD and Microdata extraction
- **Optimized Selectors**: CSS selectors for fast extraction

## 📈 Monitoring & Observability

### Health Checks
- **Liveness Probe**: `/health` endpoint
- **Readiness Probe**: `/ready` endpoint
- **Startup Probe**: Prevents premature traffic

### Metrics (Prometheus)
- **Request Metrics**: Count, duration, success rate
- **Performance Metrics**: RPS, queue size, active requests
- **Resource Metrics**: Memory, CPU usage
- **Business Metrics**: Books extracted, data quality

### Logging
- **Structured Logging**: JSON format for parsing
- **Log Levels**: Configurable verbosity
- **Context Information**: Request IDs, user agents

### Monitoring Stack (Optional)
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Pre-configured**: Book scraper dashboard included

## 🐳 Kubernetes Deployment

### Components
- **Namespace**: `book-scraper`
- **Deployment**: 3 replicas with rolling updates
- **Service**: ClusterIP with metrics annotation
- **HPA**: Auto-scaling based on CPU/memory
- **Redis**: Task queue and caching
- **ConfigMap**: Environment configuration

### Deployment Commands

```bash
# Deploy to GKE
./deploy.sh

# Manual deployment
kubectl apply -f k8s/

# Check status
kubectl get all -n book-scraper

# View logs
kubectl logs -f deployment/book-scraper -n book-scraper

# Scale deployment
kubectl scale deployment book-scraper --replicas=5 -n book-scraper
```

### Resource Requirements

- **CPU**: 250m request, 1000m limit
- **Memory**: 256Mi request, 1Gi limit
- **Storage**: Ephemeral (Redis for persistence)

## 🔒 Security Features

- **Non-root User**: Container runs as non-privileged user
- **Security Context**: Dropped capabilities, read-only root
- **Network Policies**: Pod-to-pod communication control
- **Resource Limits**: Prevents resource exhaustion
- **Health Checks**: Automatic failure detection

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Performance Tests
```bash
pytest tests/performance/
```

### Manual Testing
```bash
# Run the test script
python test_scraper.py
```

## 📚 Development

### Project Structure
```
book-scraper/
├── app/                    # Application code
│   ├── api/               # API routes
│   ├── core/              # Core scraping logic
│   ├── models/            # Data models
│   ├── monitoring/        # Metrics and monitoring
│   └── main.py           # FastAPI application
├── k8s/                   # Kubernetes manifests
├── tests/                 # Test suite
├── monitoring/            # Monitoring configuration
│   ├── prometheus.yml     # Prometheus config
│   └── grafana/          # Grafana dashboards & datasources
├── Dockerfile             # Multi-stage Docker build
├── Dockerfile.simple      # Simple Dockerfile (recommended)
├── Dockerfile.alternative # Alternative with better compatibility
├── docker-compose.yml     # Full stack with monitoring
├── docker-compose.core.yml # Core services only
├── deploy.sh              # GKE deployment script
├── requirements.txt       # Python dependencies
└── TROUBLESHOOTING.md     # Common issues and solutions
```

### Adding New Sources

1. **Extend BookSource enum**
2. **Add rate limiting rules**
3. **Implement source-specific parsing**
4. **Add tests**

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🚀 Production Deployment

### GKE Setup
1. **Enable APIs**: Container Registry, Kubernetes Engine
2. **Create Cluster**: Multi-zone with autoscaling
3. **Configure IAM**: Service account with necessary permissions
4. **Deploy**: Use provided deployment script

### Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and alerting
- **AlertManager**: Alert routing and silencing

### Scaling
- **Horizontal**: HPA based on metrics
- **Vertical**: Resource requests/limits
- **Geographic**: Multi-region deployment

## 🐛 Troubleshooting

### Common Issues

1. **Docker Build Failures**: Use `Dockerfile.simple` to avoid dependency issues
2. **Package Installation Errors**: Check package names for your base image
3. **Permission Issues**: Ensure containers run as non-root user
4. **Memory Constraints**: Increase Docker memory limits
5. **Volume Mounting**: Check if directories exist and have correct permissions

### Quick Fixes

```bash
# Use simple Dockerfile
docker build -f Dockerfile.simple -t book-scraper:latest .

# Use core services only
docker-compose -f docker-compose.core.yml up --build

# Clean Docker environment
docker system prune -a
docker-compose up --build

# Check logs
docker-compose logs book-scraper
```

### Detailed Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for comprehensive solutions to common issues.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

- **Issues**: GitHub Issues
- **Documentation**: API docs at `/docs`
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Community**: Discord/Slack (if applicable)

## 🔮 Roadmap

- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Advanced caching with Redis
- [ ] Machine learning for data quality
- [ ] Geographic distribution
- [ ] Advanced rate limiting algorithms
- [ ] Webhook notifications
- [ ] Admin dashboard
- [ ] Multi-language support

---

Built with ❤️ for high-performance book scraping and Kubernetes infrastructure experience.
