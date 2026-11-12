# LR-023 live handoff proof

Real Redis, a real Celery worker process, the real ticker and sweep, and a
real PostgreSQL built from every migration. The outside world is stubbed at
its edges only: the MLS result, the PDF renderer, R2 and webhooks inside the
worker (`worker_live.py`), and SendGrid's HTTP API (`fake_sendgrid.py`).

    DATABASE_URL=postgresql://… python scripts/live/lr023/live_run.py

It starts its own Redis on port 6391 and stops it when it finishes; the fake
SendGrid listens on 8925. The worker's Redis visibility timeout is 20 s, not
900 s, so a killed worker's message comes back within the run (Redis hands it
back on its own restore cycle, about 100 s after the kill in practice).

Steps (design §8): Redis down at the tick; Redis back and the sweep
republishes; a worker killed mid-render, its redelivery a no-op, the 6-minute
sweep's republish completing it; SendGrid accepting a POST whose answer is
lost, giving needs_review and never a resend. A transcript of a passing run is
in `docs/renders/lr-023/live-handoff.txt`.

It creates its own account and schedule, and briefly holds other due schedules
with the ticker's own lock, as the tests do. Never point it at production.
