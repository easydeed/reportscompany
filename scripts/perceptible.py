"""What would move if each template's hardcoded brand values were replaced by
derive_theme()'s tokens. CIE76 dE; 2.3 is the just-noticeable threshold."""
import sys, math
sys.path.insert(0, 'apps/worker/src')
from worker.themes import derive_theme, contrast, WHITE, normalize_hex

def lab(hexv):
    h = normalize_hex(hexv)[1:]
    r,g,b = (int(h[i:i+2],16)/255 for i in (0,2,4))
    f = lambda c: c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4
    r,g,b = f(r),f(g),f(b)
    X = (0.4124*r+0.3576*g+0.1805*b)/0.95047
    Y = (0.2126*r+0.7152*g+0.0722*b)/1.00000
    Z = (0.0193*r+0.1192*g+0.9505*b)/1.08883
    g2 = lambda t: t**(1/3) if t > 0.008856 else (7.787*t + 16/116)
    fx,fy,fz = g2(X),g2(Y),g2(Z)
    return (116*fy-16, 500*(fx-fy), 200*(fy-fz))

def dE(a,b):
    la,lb = lab(a), lab(b)
    return math.sqrt(sum((x-y)**2 for x,y in zip(la,lb)))

# (theme, primary, {role: current hardcoded value, token it maps to})
CASES = [
 ("property/teal",    "#34D1C3", [
    ("--color-primary-dark", "#21C7B7", "primary_dark"),
    ("--teal-on-light",      "#1abaae", "primary_ink"),
    ("--teal-text",          "#1a1a1a", "on_primary"),
    ("--color-row-a",        "#DFF6F3", "tint"),
 ]),
 ("property/bold",    "#0F1629", [
    ("--navy-on-light",      "#15216E", "primary_ink"),
    ("--navy-text",          "#ffffff", "on_primary"),
 ]),
 ("property/classic", "#1B365D", [
    ("--navy-on-light",      "#1B365D", "primary_ink"),
    ("--navy-text",          "#ffffff", "on_primary"),
 ]),
 ("property/modern",  "#FF6B5B", [
    ("--coral-dark",         "#bf5044", "primary_dark"),
    ("--coral-on-light",     "#d94e3f", "primary_ink"),
    ("--coral-text",         "#ffffff", "on_primary"),
 ]),
 ("property/elegant", "#1A1A1A", [
    ("--burgundy-dark",      "#0d0d0d", "primary_dark"),
    ("--burgundy-on-light",  "#1a1a1a", "primary_ink"),
    ("--burgundy-text",      "#ffffff", "on_primary"),
 ]),
 ("market (default)", "#0d9488", [
    ("--accent-on-light",    "#0d7268", "primary_ink"),
    ("--accent-on-light(m)", "#0f766e", "primary_ink"),
    ("--accent-text",        "#ffffff", "on_primary"),
 ]),
]
print(f"{'theme':18s} {'role':22s} {'ships':9s} {'token':9s} {'dE':>6s}  {'ships on white':>14s} {'token on white':>14s}")
for theme, primary, roles in CASES:
    t = derive_theme(primary)
    for role, current, token in roles:
        new = t[token]
        d = dE(current, new)
        mark = "MOVES" if d > 2.3 else "."
        cw = contrast(current, WHITE); nw = contrast(new, WHITE)
        print(f"{theme:18s} {role:22s} {current:9s} {new:9s} {d:6.2f}  {cw:13.2f}: {nw:13.2f}:  {mark}")
