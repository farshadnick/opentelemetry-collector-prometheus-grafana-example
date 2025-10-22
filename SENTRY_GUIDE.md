# Sentry Integration Guide

Complete guide for setting up and using Sentry error tracking in this observability stack.

## Quick Setup (5 Minutes)

### Step 1: Start Infrastructure
```bash
docker-compose up -d postgres redis
```
Wait about 15 seconds for services to be healthy.

### Step 2: Initialize Sentry
```bash
chmod +x sentry-init.sh
./sentry-init.sh
```

This creates:
- Database tables
- Admin user (email: admin@example.com, password: admin)

### Step 3: Start All Services
```bash
docker-compose up -d
```

### Step 4: Access Sentry
Open http://localhost:9000 and login:
- Email: `admin@example.com`
- Password: `admin`

## What Gets Sent to Sentry?

### From Flask App (Direct SDK)
- ✅ All exceptions with full stack traces
- ✅ Error context (tags, user info, custom data)
- ✅ Breadcrumbs (request flow leading to errors)
- ✅ Performance traces
- ✅ Log messages (ERROR level and above)

### From OpenTelemetry Collector
- ✅ Distributed traces
- ✅ Span data with timing
- ✅ Service-level errors

## Testing the Integration

### Test 1: Sentry Test Endpoint
```bash
curl http://localhost:5000/sentry-test
```
**Expected**: Division by zero error appears in Sentry dashboard

### Test 2: Error Endpoint
```bash
curl http://localhost:5000/error
```
**Expected**: ValueError with context tags appears in Sentry

### Test 3: Random Errors
```bash
for i in {1..20}; do curl http://localhost:5000/; done
```
**Expected**: ~2 errors (10% chance) appear in Sentry

## Viewing Errors in Sentry

1. Go to http://localhost:9000
2. Click on "Issues" in the sidebar
3. You'll see grouped errors:
   - **Exception**: Simulated error at / endpoint
   - **ValueError**: Intentional error for testing
   - **ZeroDivisionError**: From sentry-test endpoint

4. Click on any issue to see:
   - Full stack trace
   - Request details
   - Tags (endpoint, error_type)
   - Breadcrumbs
   - User context

## Sentry Features Enabled

### Exception Tracking
Every error is automatically captured with:
- Full stack trace
- Local variables
- Request context
- User information

### Breadcrumbs
See the sequence of events leading to an error:
```python
sentry_sdk.add_breadcrumb(
    category='request',
    message='Processing hello request',
    level='info',
)
```

### Custom Context
Add relevant data to errors:
```python
with sentry_sdk.push_scope() as scope:
    scope.set_tag("endpoint", "/error")
    scope.set_context("request_info", {
        "endpoint": "/error",
        "method": "GET"
    })
    sentry_sdk.capture_exception(e)
```

### Performance Monitoring
Track request timing and slow transactions:
- Every request is traced
- Transaction timing is recorded
- Slow requests are highlighted

## Architecture

```
Flask App
  ├─→ Sentry SDK ──────────────→ Sentry (Errors + Performance)
  │
  └─→ OpenTelemetry Collector ──→ Sentry (Traces)
                                 ├─→ Prometheus (Metrics)
                                 └─→ Loki (Logs)
```

## Configuration

### Flask App (app.py)
```python
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[
        FlaskIntegration(),
        LoggingIntegration(),
    ],
    traces_sample_rate=1.0,
    environment="production",
)
```

### OTel Collector (otel-collector-config.yaml)
```yaml
exporters:
  sentry:
    dsn: http://KEY@sentry:9000/1
    environment: production

service:
  pipelines:
    traces:
      exporters: [sentry]
```

### Docker Compose
- **Sentry**: Main application (port 9000)
- **PostgreSQL**: Database storage
- **Redis**: Caching and queue
- **Sentry Worker**: Background job processing
- **Sentry Cron**: Scheduled tasks

## Customizing the DSN

The default DSN is for testing. To get a real project DSN:

1. Login to Sentry: http://localhost:9000
2. Create a new project:
   - Platform: Python
   - Framework: Flask
   - Name: simple-app
3. Copy the DSN from project settings
4. Update in two places:

**docker-compose.yml:**
```yaml
app:
  environment:
    - SENTRY_DSN=http://YOUR_KEY@sentry:9000/YOUR_PROJECT_ID
```

**otel-collector-config.yaml:**
```yaml
exporters:
  sentry:
    dsn: http://YOUR_KEY@sentry:9000/YOUR_PROJECT_ID
```

5. Restart services:
```bash
docker-compose restart app otel-collector
```

## Troubleshooting

### Sentry UI Not Loading
```bash
# Check Sentry logs
docker-compose logs sentry

# Restart Sentry
docker-compose restart sentry
```

### No Errors Appearing
```bash
# Check if DSN is configured
docker-compose exec app env | grep SENTRY_DSN

# Check app logs for Sentry initialization
docker-compose logs app | grep -i sentry

# Test manually
curl http://localhost:5000/sentry-test
```

### Database Issues
```bash
# Reset everything
docker-compose down -v
docker-compose up -d postgres redis
sleep 15
./sentry-init.sh
docker-compose up -d
```

### "Table does not exist" Error
```bash
# Run migrations again
docker-compose run --rm sentry upgrade
```

## Best Practices

### 1. Add Context to Errors
Always add relevant information:
```python
with sentry_sdk.push_scope() as scope:
    scope.set_user({"id": user_id, "email": user_email})
    scope.set_tag("feature", "payment")
    scope.set_context("transaction", {"amount": 100, "currency": "USD"})
    sentry_sdk.capture_exception(e)
```

### 2. Use Breadcrumbs
Track user actions:
```python
sentry_sdk.add_breadcrumb(
    category='user_action',
    message='User clicked checkout button',
    level='info',
)
```

### 3. Filter Sensitive Data
Remove passwords, tokens, etc.:
```python
sentry_sdk.init(
    before_send=filter_sensitive_data,
)

def filter_sensitive_data(event, hint):
    if 'request' in event:
        event['request'].pop('cookies', None)
        event['request'].get('headers', {}).pop('authorization', None)
    return event
```

### 4. Set Up Alerts
In Sentry dashboard:
1. Go to Alerts → Create Alert
2. Configure conditions:
   - New issues
   - Error rate spike
   - Performance degradation
3. Set notification channels

## Advanced Features

### Release Tracking
Track errors by version:
```python
sentry_sdk.init(
    release="simple-app@1.0.0",
)
```

### User Identification
Track which users experience errors:
```python
sentry_sdk.set_user({
    "id": "12345",
    "email": "user@example.com",
    "username": "john_doe"
})
```

### Custom Tags
Organize errors:
```python
sentry_sdk.set_tag("environment", "production")
sentry_sdk.set_tag("region", "us-east-1")
sentry_sdk.set_tag("customer_tier", "premium")
```

### Performance Monitoring
Track specific operations:
```python
from sentry_sdk import start_transaction

with start_transaction(op="task", name="process_payment"):
    # Your code here
    process_payment()
```

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Sentry Dashboard | http://localhost:9000 | Error tracking UI |
| Flask App | http://localhost:5000 | Application |
| Grafana | http://localhost:3000 | Metrics/Logs |
| Prometheus | http://localhost:9090 | Metrics storage |

## Resources

- [Sentry Python Documentation](https://docs.sentry.io/platforms/python/)
- [Flask Integration](https://docs.sentry.io/platforms/python/guides/flask/)
- [OpenTelemetry Sentry Exporter](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/sentryexporter)

## Summary

Your complete observability stack now includes:
- 📊 **Metrics**: Prometheus + Grafana
- 📝 **Logs**: Loki + Grafana  
- 🔍 **Traces**: OpenTelemetry
- 🐛 **Errors**: Sentry

Happy error tracking! 🚀

