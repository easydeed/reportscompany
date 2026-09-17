import os
import ssl
from celery import Celery
from celery.schedules import crontab

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

    # ── Acknowledge when the task finishes, not when it arrives (D-062) ──────
    #
    # Celery's default acknowledges a message as soon as a pool child STARTS
    # executing it. If the worker process then dies — a deploy that outruns its
    # grace period, an OOM, a host replacement — that task is gone. Nothing
    # runs, so nothing writes a status: the schedule_runs row sits at 'queued'
    # or 'processing' forever with no error. That is the signature of the 18
    # reports D-062 traced to genuine delivery loss.
    #
    # With acks_late the message stays unacknowledged for the whole run, so a
    # lost worker returns its in-flight task to the queue instead of dropping
    # it. That is the entire point of the setting.
    #
    # PREFETCH — checked, and deliberately left alone. The worker holds
    # `worker_prefetch_multiplier` x concurrency messages beyond the one it is
    # running (default 4, unset here; measured: 4 held with concurrency 1).
    # The intuition is that acks_late makes a restart hand back a large batch
    # at once — but that is not what happens, because PREFETCHED-BUT-UNSTARTED
    # messages are unacknowledged in BOTH modes. Killing a worker mid-burst of
    # six tasks and restarting it: acks_late off, five of six completed; on,
    # six of six. The four prefetched ones came back either way. The single
    # difference is the task that was RUNNING. So prefetch does not need to
    # change alongside this, and lowering it would buy nothing here.
    #
    # THE 300s TIME LIMIT does not become a redelivery loop. A task killed at
    # the hard limit is still acknowledged, because `task_acks_on_failure_or
    # _timeout` defaults to True — verified by running it: with the default, a
    # task that blows the limit executes once; with that setting flipped to
    # False it executed 16 times in 50 seconds. Do not flip it. The limit is
    # not near firing anyway (p99 41s against 300s), but the loop is the
    # failure mode if someone changes that line, and the delivery guard would
    # NOT contain it — generate_report renders before it sends, so a task
    # killed at 300s never reaches the send and leaves no email_log row for
    # _already_delivered to match on. It would spin, not duplicate.
    #
    # WHAT THIS STILL DOES NOT COVER, measured the same way: if the POOL CHILD
    # alone is killed (an OOM kill of the child, parent surviving), the parent
    # acknowledges the message and the task is lost anyway — acks_late on, one
    # start, zero completions. Closing that needs `task_reject_on_worker_lost`,
    # which carries its own trade (a task that reliably OOMs redelivers
    # forever). Not enabled here; recorded as D-068.
    #
    # HOW FAST THE RECOVERY ARRIVES is a separate question, answered below by
    # `visibility_timeout`. Redis hands a message back only once that timeout
    # has elapsed since DELIVERY, and only when a worker happens to check.
    # Measured: a 40-second worker lifetime spanning the boundary did not
    # restore, and a subsequent start did. Restoration is opportunistic, not
    # timely — so the timeout is a floor on the delay, not the delay itself.
    #
    # THIS IS NOT INTRODUCED BY THE LINE BELOW, which is the important part.
    # Prefetched-but-unstarted messages are unacknowledged in BOTH modes, so
    # they already strand this way today — and that is the only mechanism found
    # that can put a report in an inbox on a different day from its run, which
    # is what D-064's mailbox check turned up. Enabling late acks extends an
    # existing behaviour to the running task; it does not create a new one.
    "task_acks_late": True,

    # ── How long Redis waits before handing a message back (D-070) ──────────
    #
    # Was unset, so kombu's default of 3600s applied: a stranded report could
    # not reappear for at least an hour, and in practice not until whichever
    # worker start first looked after that hour — which is deploy-driven, so
    # days were possible. That is the mechanism behind D-064's reports arriving
    # on a different date from their runs.
    #
    # This number is two things at once, which is why the default was wrong in
    # both directions:
    #
    #   as a RECOVERY DELAY   shorter is better — it floors how late a
    #                         stranded report can arrive
    #   as a LEASE on a task  shorter is worse — go below the longest
    #                         legitimate run and a SECOND worker picks up work
    #                         the first is still doing: a duplicate execution,
    #                         not a slow one
    #
    # THE LEASE SIDE HAS A HARD FLOOR AND WE KNOW IT EXACTLY. No task can
    # outlive `task_time_limit` above; the hard kill guarantees it. So any
    # value comfortably over 300s cannot hand live work to a second worker,
    # whatever the p99 does. That is a guarantee rather than a percentile,
    # which is why it is the right basis. 900s is 3x the ceiling — the same
    # margin STALE_STARTED_MINUTES (6 min) already takes against the same
    # limit, so the two agree rather than each guessing separately.
    #
    # NEVER SET THIS BELOW 300s. That is not tuning; it discards the guarantee
    # the time limit provides, and the failure it buys is the unrecallable one.
    "broker_transport_options": {"visibility_timeout": 900},

    # Celery Beat schedule for periodic tasks
    "beat_schedule": {
        "keep-alive-ping": {
            "task": "keep_alive_ping",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
}

# Add SSL configuration if using secure Redis (rediss://)
if SSL_CONFIG:
    config_updates["broker_use_ssl"] = SSL_CONFIG
    config_updates["redis_backend_use_ssl"] = SSL_CONFIG

celery.conf.update(**config_updates)

# Import tasks to register them with Celery
from . import tasks  # noqa
from .property_tasks import property_report  # noqa - property report generation tasks

