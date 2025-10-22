#!/bin/bash

# Sentry initialization script
# This script sets up Sentry for the first time

echo "🔧 Initializing Sentry..."
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Run Sentry upgrade (creates database tables)
echo "📦 Running Sentry database migrations..."
docker-compose run --rm sentry upgrade --noinput

echo ""
echo "✨ Sentry database setup complete!"
echo ""
echo "Now creating a superuser account..."
echo ""

# Create superuser
docker-compose run --rm sentry createuser \
  --email admin@example.com \
  --password admin \
  --superuser \
  --no-input

echo ""
echo "✅ Sentry setup complete!"
echo ""
echo "📊 Access Sentry at: http://localhost:9000"
echo "   Email: admin@example.com"
echo "   Password: admin"
echo ""
echo "Next steps:"
echo "1. Log in to Sentry"
echo "2. Create a new project (Python/Flask)"
echo "3. Copy the DSN and update docker-compose.yml"
echo "4. Restart the services: docker-compose restart app otel-collector"
echo ""

