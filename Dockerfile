# Use Python 3.10 slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create www-data user if it doesn't exist
RUN usermod -u 1000 www-data

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install uWSGI
RUN pip install uwsgi

# Copy project files
COPY . /app/

# Copy configuration files
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY uwsgi.ini /app/uwsgi.ini

# Create necessary directories
RUN mkdir -p /var/log /app/staticfiles /app/media

# Set permissions
RUN chown -R www-data:www-data /app /var/log
RUN chmod +x /app/manage.py

# Collect static files
RUN python manage.py collectstatic --noinput

# Create entrypoint script
RUN echo '#!/bin/bash\n\
# Run migrations\n\
python manage.py migrate --noinput\n\
\n\
# Load fixtures if they exist\n\
if [ -f "/app/fixtures/users.json" ]; then\n\
    python manage.py loaddata fixtures/users.json || true\n\
fi\n\
if [ -f "/app/fixtures/assets.json" ]; then\n\
    python manage.py loaddata fixtures/assets.json || true\n\
fi\n\
if [ -f "/app/fixtures/purchases.json" ]; then\n\
    python manage.py loaddata fixtures/purchases.json || true\n\
fi\n\
if [ -f "/app/fixtures/simulated_nfts.json" ]; then\n\
    python manage.py loaddata fixtures/simulated_nfts.json || true\n\
fi\n\
if [ -f "/app/fixtures/payment_logs.json" ]; then\n\
    python manage.py loaddata fixtures/payment_logs.json || true\n\
fi\n\
if [ -f "/app/fixtures/benefit_rules.json" ]; then\n\
    python manage.py loaddata fixtures/benefit_rules.json || true\n\
fi\n\
\n\
# Start supervisord\n\
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Switch to www-data user
USER www-data

# Run entrypoint
CMD ["/app/entrypoint.sh"]