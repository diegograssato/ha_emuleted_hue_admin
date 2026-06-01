ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.13-alpine3.19

FROM ${BUILD_FROM}

# Labels
LABEL \
  io.hass.name="Emulated Hue Manager" \
  io.hass.description="Visual manager for Home Assistant Emulated Hue configuration" \
  io.hass.type="addon" \
  maintainer="Diego Grassato"

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/

WORKDIR /

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy application source
COPY rootfs/app /app

# Data directory
RUN mkdir -p /data/backups

# Expose port
EXPOSE 8099

# Override s6-overlay entrypoint — run uvicorn directly as PID 1
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8099", "--workers", "1", "--log-level", "info"]


