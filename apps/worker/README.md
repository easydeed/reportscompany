# Market Reports Worker

## Dev
poetry install
# install browser for Playwright locally
poetry run python -m playwright install chromium
# run worker
poetry run celery -A worker.app.celery worker -l info

## Test ping task
poetry run python -c "from worker.tasks import ping; r=ping.delay(); print(r.get(timeout=10))"

