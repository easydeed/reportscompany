#!/usr/bin/env python3
"""Generate the 4 transactional notification emails for visual review."""

import os, platform, subprocess
from pathlib import Path

APP_BASE = "https://www.trendyreports.io"
EMAIL_PY = Path(__file__).resolve().parent.parent / "apps" / "api" / "src" / "api" / "services" / "email.py"
OUT = Path(__file__).resolve().parent.parent / "output" / "transactional_emails"
OUT.mkdir(parents=True, exist_ok=True)


def _load_funcs():
    """Load _email_base, _cta_button, and the 3 get_*_html functions from email.py."""
    lines = EMAIL_PY.read_text(encoding="utf-8").split("\n")

    # Find "def _email_base" (line 172, 0-indexed 171) through the end of
    # get_password_reset_email_html which ends with "return _email_base(content)"
    start_idx = next(i for i, l in enumerate(lines) if "def _email_base(" in l)

    # End right after the last "return _email_base(content)" in the file
    end_idx = start_idx
    for i in range(start_idx, len(lines)):
        if "return _email_base(content)" in lines[i]:
            end_idx = i

    func_source = "\n".join(lines[start_idx:end_idx + 1])

    # The extracted range includes send_* functions that reference typing + email_service
    preamble = (
        "from typing import Optional, Dict, Any, List\n"
        f"class _S:\n"
        f"    app_base = '{APP_BASE}'\n"
        f"    def send_email_sync(self, **kw): return {{}}\n"
        "email_service = _S()\n\n"
    )
    ns = {}
    exec(compile(preamble + func_source, "<transactional>", "exec"), ns)
    return ns


EMAILS = [
    ("get_verification_email_html", "01_verification.html",
     "Welcome + Verify Email", "Sent when a new user signs up",
     {"user_name": "Sarah Chen", "verify_url": f"{APP_BASE}/verify-email?token=sample-token"}),
    ("get_invite_email_html", "02_invite.html",
     "Agent Invite", "Affiliate invites a sponsored agent",
     {"inviter_name": "Jerry Hernandez", "company_name": "Demo Title Company",
      "invite_url": f"{APP_BASE}/welcome?token=sample-invite-token"}),
    ("get_password_reset_email_html", "03_password_reset.html",
     "Password Reset", "User requests a password reset",
     {"user_name": "Sarah Chen", "reset_url": f"{APP_BASE}/reset-password?token=sample-reset-token"}),
]

ns = _load_funcs()
rows = ""
for func, fname, label, trigger, kwargs in EMAILS:
    html = ns[func](**kwargs)
    (OUT / fname).write_text(html, encoding="utf-8")
    print(f"  [OK] {label:25s} -> {fname}")
    rows += f"""
    <tr>
      <td style="padding:14px 18px;border-bottom:1px solid #f1f5f9;font-weight:600;color:#1e293b;">{label}</td>
      <td style="padding:14px 18px;border-bottom:1px solid #f1f5f9;color:#64748b;font-size:13px;">{trigger}</td>
      <td style="padding:14px 18px;border-bottom:1px solid #f1f5f9;">
        <a href="{fname}" target="_blank" style="color:#7C3AED;text-decoration:none;font-weight:500;">Open &rarr;</a>
      </td>
    </tr>"""

index_html = f"""<!DOCTYPE html>
<html><head><title>Transactional Emails — TrendyReports</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 720px; margin: 48px auto; padding: 0 24px; color: #1e293b; }}
  h1 {{ font-size: 24px; margin-bottom: 4px; }}
  .sub {{ color: #64748b; margin-bottom: 28px; font-size: 14px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  th {{ text-align: left; padding: 12px 18px; background: #f8fafc; font-size: 11px; text-transform: uppercase;
       letter-spacing: 0.5px; color: #64748b; border-bottom: 2px solid #e2e8f0; }}
  tr:hover {{ background: #faf5ff; }}
</style></head><body>
<h1>Transactional Emails</h1>
<p class="sub">3 notification types &bull; Sent via Resend &bull; Click to open in new tab</p>
<table>
  <thead><tr><th>Email</th><th>Trigger</th><th></th></tr></thead>
  <tbody>{rows}</tbody>
</table>
</body></html>"""

idx = OUT / "index.html"
idx.write_text(index_html, encoding="utf-8")
print(f"\n  Index: {idx}")

if platform.system() == "Windows":
    os.startfile(str(idx))
elif platform.system() == "Darwin":
    subprocess.run(["open", str(idx)])
else:
    subprocess.run(["xdg-open", str(idx)])
