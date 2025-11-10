# Market Reports Worker - Production Dockerfile
# Uses Microsoft's official Playwright Python image with Chromium pre-installed
# This ensures all browser dependencies are present and eliminates sudo/permission issues

FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock ./

# Configure Poetry to create virtualenv in project and install dependencies
# --no-root: Don't install the project itself (we'll copy code after)
# --no-interaction: Non-interactive mode for CI/CD
# --no-ansi: Disable colored output for cleaner logs
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --no-interaction --no-ansi

# Copy application source code
COPY src/ ./src/

# Set Python path so imports work correctly
ENV PYTHONPATH=/app/src

# Playwright browsers are already installed in the base image at /ms-playwright
# No need to run `playwright install` - saves build time and avoids issues

# Health check to ensure Celery worker is responsive
# Checks every 30 seconds, times out after 10s, waits 5s before starting checks
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD poetry run python -c "from worker.app import celery; celery.control.inspect().active() or exit(1)"

# Start Celery worker
# -A: Application module
# worker: Run worker mode
# -l info: Log level INFO
CMD ["poetry", "run", "celery", "-A", "worker.app.celery", "worker", "-l", "info"]

