# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /usr/src/app

ARG SUPERVISORD_CONFIG=supervisord.vps.conf

# Install system dependencies for building Python libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    libpcre3 \
    libpcre3-dev \
    libssl-dev \
    libffi-dev \
    supervisor \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* 

# Create necessary directories
RUN mkdir -p /usr/src/app/gaspack_rwa /var/log/uwsgi /usr/src/app/gaspack_rwa/static /usr/src/app/gaspack_rwa/media

# Copy the requirements file into the container
COPY gaspack_rwa/requirements.txt /usr/src/app/gaspack_rwa/
RUN ls -la /usr/src/app/gaspack_rwa/requirements.txt

# Install Python dependencies with binary wheels
RUN pip install --no-cache-dir -r /usr/src/app/gaspack_rwa/requirements.txt
RUN pip install --no-cache-dir uwsgi

# Download spacy model
RUN python -m spacy download en_core_web_sm

# Copy the application code into the container
COPY gaspack_rwa/ /usr/src/app/gaspack_rwa/
RUN ls -la /usr/src/app/gaspack_rwa/

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=monitoring_host.settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/usr/src/app/gaspack_rwa

# Collect static files
RUN cd /usr/src/app/gaspack_rwa && python manage.py collectstatic --noinput

# Set proper permissions
RUN chown -R www-data:www-data /usr/src/app/gaspack_rwa /var/log/uwsgi
RUN chmod -R 755 /usr/src/app/gaspack_rwa

# Expose port for uWSGI/Django
EXPOSE 8001

# Create supervisor directory and copy configuration
RUN mkdir -p /etc/supervisor/conf.d
COPY gaspack_rwa/${SUPERVISORD_CONFIG} /etc/supervisor/conf.d/supervisord.conf

RUN ls -la /etc/supervisor/conf.d/supervisord.conf

# Run Supervisor to manage processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 