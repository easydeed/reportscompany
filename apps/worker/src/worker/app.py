import os
import ssl
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_URL = os.getenv("CELERY_RESULT_URL", REDIS_URL)

# For Celery, we need to strip the ssl_cert_reqs from the URL
# and configure it via broker_use_ssl and redis_backend_use_ssl parameters
if "ssl_cert_reqs=" in REDIS_URL:
    # Remove the parameter for Celery (both broker and backend)
    BROKER = REDIS_URL.split("?")[0]
    BACKEND = CELERY_RESULT_URL.split("?")[0] if "ssl_cert_reqs=" in CELERY_RESULT_URL else CELERY_RESULT_URL
    
    # Celery requires SSL config as a dictionary
    SSL_CONFIG = {
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None
    }
else:
    BROKER = REDIS_URL
    BACKEND = CELERY_RESULT_URL
    SSL_CONFIG = None

celery = Celery(
    "market_reports",
    broker=BROKER,
    backend=BACKEND,
)

# Base configuration
config_updates = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_routes": {
        "ping": {"queue": "celery"},
    },
    "task_time_limit": 300,
}

# Add SSL configuration if using secure Redis (rediss://)
if SSL_CONFIG:
    config_updates["broker_use_ssl"] = SSL_CONFIG
    config_updates["redis_backend_use_ssl"] = SSL_CONFIG

celery.conf.update(**config_updates)

# Import tasks to register them with Celery
from . import tasks  # noqa
from .property_tasks import property_report  # noqa - property report generation tasks

