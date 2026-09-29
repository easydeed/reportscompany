import sys
from pathlib import Path
from jinja2 import Environment, nodes
REPO = Path("/home/user/reportscompany")
T = REPO / "apps/worker/src/worker/templates"
env = Environment()

def dotted(node):
    parts = []
    while isinstance(node, nodes.Getattr):
        parts.append(node.attr); node = node.node
    if isinstance(node, nodes.Name):
        parts.append(node.name)
        return ".".join(reversed(parts))
    return None

for path in sorted(T.rglob("*.jinja2")):
    src = path.read_text(encoding="utf-8")
    try:
        ast_ = env.parse(src)
    except Exception as e:
        print("PARSE FAIL", path, e); continue
    for n in ast_.find_all(nodes.If):
        d = dotted(n.test)
        if d is None: continue
        has_else = bool(n.else_) or bool(n.elif_)
        print(f"{path.relative_to(T)}:{n.lineno} {d} else={has_else}")
