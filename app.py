from flask import Flask, jsonify
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
import logging
import random
import time

# Configure OpenTelemetry Resource
resource = Resource.create({"service.name": "simple-app"})

# Configure logging with OpenTelemetry
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

# Add OTLP Log Exporter
otlp_log_exporter = OTLPLogExporter(endpoint="http://otel-collector:4317", insecure=True)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

# Configure Python logging to use OpenTelemetry handler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
logger.addHandler(handler)

# Configure tracing
trace_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace_provider.add_span_processor(span_processor)
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Configure metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://otel-collector:4317", insecure=True)
)
metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
meter = metrics.get_meter(__name__)

# Create metrics
request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total number of HTTP requests",
    unit="1"
)

request_duration = meter.create_histogram(
    name="http_request_duration_seconds",
    description="HTTP request duration in seconds",
    unit="s"
)

active_users = meter.create_up_down_counter(
    name="active_users",
    description="Number of active users",
    unit="1"
)

error_counter = meter.create_counter(
    name="http_errors_total",
    description="Total number of HTTP errors",
    unit="1"
)

memory_usage = meter.create_observable_gauge(
    name="memory_usage_bytes",
    description="Memory usage in bytes",
    unit="bytes",
    callbacks=[lambda: random.randint(1000000, 2000000)]  # Simulated memory usage
)

cpu_usage = meter.create_observable_gauge(
    name="cpu_usage_percent",
    description="CPU usage percentage",
    unit="percent",
    callbacks=[lambda: random.uniform(10, 90)]  # Simulated CPU usage
)

# Create Flask application
app = Flask(__name__)

logger.info("Application starting up...")

@app.route('/')
def hello():
    logger.info("Received request to / endpoint")
    with tracer.start_as_current_span("hello_operation") as span:
        span.set_attribute("operation.type", "hello")
        
        # Simulate some processing time
        sleep_time = random.uniform(0.1, 0.5)
        logger.debug(f"Processing request, sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
        
        # Record metrics
        request_counter.add(1, {"endpoint": "/", "method": "GET"})
        request_duration.record(sleep_time, {"endpoint": "/"})
        
        # Simulate user activity
        active_users.add(random.randint(-1, 1))
        
        # Simulate occasional errors
        if random.random() < 0.1:  # 10% chance of error
            logger.error("Simulated error occurred at / endpoint", extra={"endpoint": "/", "error_type": "simulated"})
            error_counter.add(1, {"endpoint": "/", "error_type": "simulated"})
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            return jsonify({"error": "Simulated error"}), 500
        
        logger.info("Successfully processed request to / endpoint")
        return jsonify({"message": "Hello, OpenTelemetry!"})

@app.route('/metrics')
def metrics_endpoint():
    logger.info("Received request to /metrics endpoint")
    with tracer.start_as_current_span("metrics_operation") as span:
        span.set_attribute("operation.type", "metrics")
        
        # Simulate some processing time
        sleep_time = random.uniform(0.2, 0.8)
        logger.debug(f"Fetching metrics, processing time: {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
        
        # Record metrics
        request_counter.add(1, {"endpoint": "/metrics", "method": "GET"})
        request_duration.record(sleep_time, {"endpoint": "/metrics"})
        
        # Simulate user activity
        active_users.add(random.randint(-1, 1))
        
        metrics_data = {
            "active_users": random.randint(50, 200),
            "memory_usage": random.randint(1000000, 2000000),
            "cpu_usage": random.uniform(10, 90)
        }
        logger.info(f"Returning metrics data: active_users={metrics_data['active_users']}, memory_usage={metrics_data['memory_usage']}")
        
        return jsonify(metrics_data)

@app.route('/error')
def error_endpoint():
    logger.warning("Received request to /error endpoint - intentional error simulation")
    with tracer.start_as_current_span("error_operation") as span:
        span.set_attribute("operation.type", "error")
        
        # Record metrics
        request_counter.add(1, {"endpoint": "/error", "method": "GET"})
        error_counter.add(1, {"endpoint": "/error", "error_type": "simulated"})
        
        # Set error status
        span.set_status(trace.Status(trace.StatusCode.ERROR))
        
        logger.error("Intentional error raised at /error endpoint", extra={"endpoint": "/error", "status_code": 500})
        
        return jsonify({"error": "Simulated error"}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application on port 5000")
    app.run(host='0.0.0.0', port=5000)
