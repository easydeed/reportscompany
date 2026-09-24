#!/usr/bin/env python3
"""Does PDFShift actually require header.start_at == footer.start_at? (D-103)

WHY THIS EXISTS. `tasks.py` states, in a comment, that "PDFShift requires
header.start_at and footer.start_at to match when either > 1", and passes 1 for
both. Master plan §7.1 wants a full masthead on page 1 and a one-line running
head on every page after — which is a header starting at page 2. If the
constraint is real, that also pushes the FOOTER off page 1, and §7.1's
architecture has to be built a different way (masthead in the body for page 1).
The whole page design rests on it.

It is a code comment, not a measurement. Nobody has watched PDFShift refuse it.

WHAT THIS DOES. Renders the same four-page document four ways and reports what
comes back each time:

    A  header.start_at 1, footer.start_at 1   (what ships today — the control)
    B  header.start_at 2, footer.start_at 2   (matched, both > 1)
    C  header.start_at 2, footer.start_at 1   (SPLIT — the case in question)
    D  header.start_at 1, footer.start_at 2   (split the other way)

For each: the HTTP status, any error body, the page count, and — when it
renders — which pages carry the header and footer, detected by searching each
page's text for marker strings unique to each. So the answer is what PDFShift
did, not what it accepted.

WHAT COUNTS AS AN ANSWER.
  * C and D rejected (4xx naming start_at)  -> the constraint is real; §7.1
    needs the masthead in the body for page 1.
  * C and D accepted AND the markers land where asked -> the constraint is not
    real, the comment is wrong, and §7.1 can be built the obvious way.
  * C and D accepted but the markers do NOT land where asked -> worse than a
    refusal, because today's code would silently do the wrong thing. Report
    exactly which pages got what.

    PDFSHIFT_API_KEY=... python3 scripts/probe_pdfshift_start_at.py

Costs four conversions against the account.
"""

import json
import os
import sys
import tempfile

API = "https://api.pdfshift.io/v3/convert/pdf"
HEADER_MARKER = "ZZHEADERMARKERZZ"
FOOTER_MARKER = "ZZFOOTERMARKERZZ"

BODY = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  @page { size: Letter; margin: 0; }
  .p { height: 9in; page-break-after: always; font: 48px sans-serif; padding: 1in; }
</style></head><body>
  <div class="p">BODY PAGE ONE</div>
  <div class="p">BODY PAGE TWO</div>
  <div class="p">BODY PAGE THREE</div>
  <div class="p">BODY PAGE FOUR</div>
</body></html>"""

HEADER = f'<!DOCTYPE html><html><body style="margin:0;font:14px sans-serif">{HEADER_MARKER}</body></html>'
FOOTER = f'<!DOCTYPE html><html><body style="margin:0;font:14px sans-serif">{FOOTER_MARKER}</body></html>'

CASES = [
    ("A control  header@1 footer@1", 1, 1),
    ("B matched  header@2 footer@2", 2, 2),
    ("C SPLIT    header@2 footer@1", 2, 1),
    ("D SPLIT    header@1 footer@2", 1, 2),
]


def main():
    key = os.environ.get("PDFSHIFT_API_KEY")
    if not key:
        sys.exit("PDFSHIFT_API_KEY is required. This probe cannot be faked — the "
                 "question is what PDFShift does, and only PDFShift can answer it.")
    import httpx
    from pypdf import PdfReader

    out = tempfile.mkdtemp(prefix="pdfshift-start-at-")
    for label, h_at, f_at in CASES:
        payload = {
            "source": BODY, "sandbox": False, "use_print": True, "format": "Letter",
            "margin": {"top": "0.1in", "right": "0", "bottom": "0.1in", "left": "0"},
            "remove_blank": True, "delay": 500, "wait_for_network": True,
            "header": {"source": HEADER, "height": "1.0in", "start_at": h_at},
            "footer": {"source": FOOTER, "height": "0.8in", "start_at": f_at},
        }
        r = httpx.post(API, json=payload, timeout=120.0,
                       headers={"X-API-Key": key, "Content-Type": "application/json",
                                "X-Processor-Version": "142"})
        if r.status_code >= 400:
            try:
                detail = json.dumps(r.json())[:400]
            except Exception:
                detail = r.text[:400]
            print(f"{label}  REJECTED {r.status_code}  {detail}")
            continue

        path = os.path.join(out, label.split()[0] + ".pdf")
        with open(path, "wb") as fh:
            fh.write(r.content)
        reader = PdfReader(path)
        head_on, foot_on = [], []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if HEADER_MARKER in text:
                head_on.append(i)
            if FOOTER_MARKER in text:
                foot_on.append(i)
        asked_h = list(range(h_at, len(reader.pages) + 1))
        asked_f = list(range(f_at, len(reader.pages) + 1))
        verdict = "as asked" if (head_on == asked_h and foot_on == asked_f) else "*** NOT AS ASKED ***"
        print(f"{label}  OK  {len(reader.pages)} pages  "
              f"header on {head_on} (asked {asked_h})  "
              f"footer on {foot_on} (asked {asked_f})  {verdict}")

    print(f"\nPDFs in {out}")
    print("Record the verdict on D-103 and in master plan §7.1 with the date it was run.")


if __name__ == "__main__":
    main()
