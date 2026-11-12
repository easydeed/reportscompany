"""A real Celery worker for the LR-023 live run, with the outside world stubbed.

Everything between the broker and SendGrid is the shipped code. Stubbed at the
edges only: the MLS result (served from the report cache), the PDF renderer and
R2 upload, outbound webhooks and failure notices. SendGrid's HTTP API is the
fake in fake_sendgrid.py. The Redis visibility timeout is 20 s instead of 900 s,
so a killed worker's unacknowledged message comes back within the run.

control.json's "render_sleep" makes the render take that many seconds, so the
driver can kill the worker while it holds a run.
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/worker/src"))

from worker.app import celery  # noqa: E402
from worker import tasks  # noqa: E402
import worker.market_builder as market_builder  # noqa: E402
from worker.email.providers import sendgrid  # noqa: E402

RESULT = {
    "matched": 12, "report_type": "market_snapshot", "city": "Glendora",
    "counts": {"Active": 12, "Closed": 8, "Pending": 3},
    "metrics": {"median_close_price": 905000, "avg_dom": 21, "months_of_supply": 1.9},
    "total_listings": 12, "total_shown": 3,
}


class Builder:
    def __init__(self, data):
        self.data = data

    def render_html(self):
        return "<html><body>report</body></html>"

    def render_page_header_html(self):
        return ""

    def render_page_footer_html(self):
        return ""


def render(run_id, **kw):
    secs = json.loads((HERE / "control.json").read_text()).get("render_sleep", 0)
    if secs:
        print(f"LIVE render of {run_id} sleeping {secs}s", flush=True)
        time.sleep(secs)
    path = HERE / f"{run_id}.pdf"
    path.write_bytes(b"%PDF-1.4 live")
    return str(path), None


tasks.cache_get = lambda *a, **k: dict(RESULT)
tasks.cache_set = lambda *a, **k: None
tasks.proxy_report_photos_inplace = lambda *a, **k: None
tasks.embed_images_as_base64 = lambda html: html
tasks._deliver_webhooks = lambda *a, **k: None
tasks._send_failure_notification = lambda **k: None
tasks.render_pdf = render
tasks.upload_to_r2 = lambda path, key, *a, **k: f"https://r2.test/{key}"
market_builder.MarketReportBuilder = Builder
sendgrid.SENDGRID_API_URL = f"http://127.0.0.1:{os.environ['FAKE_SENDGRID_PORT']}/v3/mail/send"
sendgrid.SENDGRID_API_KEY = "SG.live-run-not-a-real-key"
sendgrid.SENDGRID_TIMEOUT = 3.0
celery.conf.broker_transport_options = {"visibility_timeout": 20}

if __name__ == "__main__":
    celery.worker_main(["worker", "--loglevel=INFO", "--pool=solo", "-Q", "celery",
                        "--without-gossip", "--without-mingle", "-n", f"live-{os.getpid()}@local"])
