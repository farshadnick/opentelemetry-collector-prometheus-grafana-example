# OpenTelemetry Collector + Prometheus + Grafana + Loki Example

This project demonstrates a complete observability stack with:
- **OpenTelemetry Collector** for collecting traces, metrics, and logs
- **Prometheus** for storing metrics
- **Grafana Loki** for storing logs
- **Grafana** for visualizing metrics and logs
- **Flask Application** generating sample telemetry data

## Architecture
+--------------------+
|   Flask App        |
|  (OpenTelemetry)   |
|                    |
|  - OTLP Export     |----> gRPC/HTTP (4317/4318)
|  - /metrics        |----> Prometheus Scrape
+---------+----------+
          |
          v
+---------+----------+
| OpenTelemetry      |
|     Collector      |
|                    |
| Receivers:         |
|   • OTLP           |
|   • Prometheus     |
| Processors:        |
|   • batch          |
| Exporters:         |
|   • Prometheus --> +------------------+
|   • Loki       --> +--------------+   |
+---------+----------+              |   |
          |                         |   |
          v                         v   v
+---------+----------+     +--------+--------+
|   Prometheus       |     |      Loki       |
| (Metrics Storage)  |     |  (Logs Storage) |
+---------+----------+     +--------+--------+
          |                         |
          |                         |
          v                         v
     +----+-------------------------+----+
     |            Grafana               |
     | - Metrics from Prometheus        |
     | - Logs from Loki                 |
     +----------------------------------+

## Prerequisites

- Docker
- Docker Compose

## Getting Started

### 1. Start the Stack

```bash
docker-compose up -d
```

This will start:
- Flask app on http://localhost:5000
- OpenTelemetry Collector on ports 4317 (gRPC) and 4318 (HTTP)
- Prometheus on http://localhost:9090
- Loki on http://localhost:3100
- Grafana on http://localhost:3000

### 2. Access Grafana

1. Open http://localhost:3000
2. Login with:
   - Username: `admin`
   - Password: `admin`
3. The dashboard "Simple App Dashboard" should be automatically provisioned

### 3. Generate Some Traffic

Run the traffic generator script to create logs, metrics, and traces:

```bash
python generate_traffic.py
```

Or manually make requests:

```bash
# Normal requests
curl http://localhost:5000/

# Metrics endpoint
curl http://localhost:5000/metrics

# Error endpoint (generates errors)
curl http://localhost:5000/error
```

### 4. View Logs in Grafana

1. In Grafana, click on "Explore" (compass icon) in the left sidebar
2. Select "Loki" as the data source
3. Use LogQL queries to explore logs:
   ```
   {service_name="simple-app"}
   ```
   
4. Filter by log level:
   ```
   {service_name="simple-app"} |= "ERROR"
   {service_name="simple-app"} |= "INFO"
   ```

### 5. View Metrics in Grafana

The pre-configured dashboard includes:
- Request Rate
- Average Request Duration
- Active Users
- CPU Usage
- Memory Usage
- Error Rate

## Application Endpoints

- `GET /` - Returns a hello message with 10% chance of error
- `GET /metrics` - Returns simulated metrics data
- `GET /error` - Always returns an error (for testing)

## Logs Generated

The application generates logs for:
- Application startup
- Each incoming request (INFO level)
- Processing details (DEBUG level)
- Errors (ERROR level)
- Warnings (WARNING level)

## Configuration Files

- `docker-compose.yml` - Orchestrates all services
- `otel-collector-config.yaml` - OpenTelemetry Collector configuration
- `loki-config.yaml` - Grafana Loki configuration
- `prometheus.yml` - Prometheus configuration
- `grafana-provisioning/` - Grafana auto-provisioning configs

## Stopping the Stack

```bash
docker-compose down
```

To remove volumes as well:

```bash
docker-compose down -v
```

## Troubleshooting

### Check Service Logs

```bash
# Check all services
docker-compose logs

# Check specific service
docker-compose logs app
docker-compose logs otel-collector
docker-compose logs loki
docker-compose logs grafana
docker-compose logs prometheus
```

### Verify OpenTelemetry Collector

The collector debug exporter will print received telemetry to console:
```bash
docker-compose logs otel-collector
```

### Test Loki Directly

```bash
# Check Loki is ready
curl http://localhost:3100/ready

# Query logs directly
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={service_name="simple-app"}' | jq
```

### Test Prometheus

Visit http://localhost:9090 and query:
- `http_requests_total`
- `http_request_duration_seconds`
- `active_users`
- `cpu_usage_percent`
- `memory_usage_bytes`

## Technologies Used

- **Python 3.9** with Flask
- **OpenTelemetry SDK** for instrumentation
- **OpenTelemetry Collector Contrib** for telemetry pipeline
- **Prometheus** for metrics storage
- **Grafana Loki** for log aggregation
- **Grafana** for visualization
- **Docker & Docker Compose** for containerization

## License

MIT

