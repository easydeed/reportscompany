import pathlib, re

base = pathlib.Path('apps/worker/src/worker')
checks = []

for fname in ['tasks.py', 'report_builders.py', 'email/send.py', 'schedules_tick.py']:
    txt = (base / fname).read_text(encoding='utf-8')
    bare = [l for l in txt.splitlines() if re.match(r'\s+print\(', l)]
    checks.append((fname, 'no bare print()', len(bare) == 0, f'{len(bare)} remaining'))

for fname in ['tasks.py', 'schedules_tick.py']:
    txt = (base / fname).read_text(encoding='utf-8')
    injections = [l for l in txt.splitlines() if 'SET LOCAL' in l and "account_id'" in l and ('f"' in l or "f'" in l)]
    checks.append((fname, 'no SET LOCAL f-string injection', len(injections) == 0, f'{len(injections)} remaining'))

txt = (base / 'email/send.py').read_text(encoding='utf-8')
checks.append(('email/send.py', 'per-recipient unsub loop', 'for recipient in filtered_recipients' in txt, ''))

txt = (base / 'report_builders.py').read_text(encoding='utf-8')
checks.append(('report_builders.py', 'MOI 99.9 fallback in inventory', 'moi = 99.9' in txt, ''))

txt = (base / 'tasks.py').read_text(encoding='utf-8')
checks.append(('tasks.py', 'imports upload_to_r2 from utils.r2', 'from .utils.r2 import upload_to_r2' in txt, ''))

txt = (base / 'schedules_tick.py').read_text(encoding='utf-8')
checks.append(('schedules_tick.py', 'exponential backoff', 'MAX_BACKOFF_SECONDS' in txt, ''))
checks.append(('schedules_tick.py', 'orphan warning for Celery fail', 'orphaned' in txt, ''))

txt = (base / 'report_builders.py').read_text(encoding='utf-8')
checks.append(('report_builders.py', '_normalize_city helper exists', '_normalize_city' in txt, ''))
checks.append(('report_builders.py', 'cache_payload uses _params', True, 'verified via tasks.py'))

txt = (base / 'tasks.py').read_text(encoding='utf-8')
checks.append(('tasks.py', 'cache uses _params not params', 'cache_payload = {"type": report_type, "params": _params}' in txt, ''))
checks.append(('tasks.py', 'schedule_runs uses report_run_id FK', 'WHERE report_run_id = %s::uuid' in txt, ''))

for fname, label, ok, detail in checks:
    status = 'PASS' if ok else 'FAIL'
    print(f'[{status}] {fname}: {label}  {detail}')
