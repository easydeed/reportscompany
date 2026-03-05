# Cursor Prompt: Fix Email Template Colors

## The Problem

The email templates in `template.py` have two issues:

### Issue 1: Hardcoded Colors
All colors are hardcoded (e.g., `#1B365D`, `#B8860B`). They must be parameterized using f-string variables `{primary_color}` and `{accent_color}` so each agent's brand colors flow through.

### Issue 2: Dark Background
The body and outer email container use `background-color: #f5f5f4` (light gray). Combined with the dark navy primary color appearing everywhere, the email feels dark and heavy. The body should be WHITE.

---

## Fix 1: Background Colors

### Change these backgrounds to WHITE:

```python
# Body tag
# BEFORE:
'background-color: #f5f5f4'
# AFTER:
'background-color: #ffffff'

# Outer email container table
# BEFORE:
'background-color: #f5f5f4;'
# AFTER:
'background-color: #f0efed;'  # Very light warm gray for the "behind the email" area
# NOTE: This is the area OUTSIDE the 600px email card. A subtle gray here
# creates the "floating card" effect. But inside the email = pure white.

# Content area (already correct in most templates)
'background-color: #ffffff;'  # KEEP — this is the main email body

# Footer area
# BEFORE:
'background-color: #f9fafb'
# AFTER:
'background-color: #fafaf9'  # Very subtle warm gray, acceptable for footer
```

### Summary of background rules:
| Area | Color | Notes |
|------|-------|-------|
| `<body>` | `#f0efed` | Light warm gray behind the email card |
| Outer `<table>` wrapper | `#f0efed` | Same as body |
| Content `<td>` (main body) | `#ffffff` | Pure white — always |
| Card backgrounds | `#ffffff` | White cards on white body |
| Footer `<td>` | `#fafaf9` | Barely-there warm gray |
| Agent footer container | `{primary_color}08` | Very subtle brand tint — keep |
| CTA area | `{primary_color}0A` | Very subtle brand tint — keep |
| Quick Take | `{accent_color}0F` | Very subtle accent tint — keep |

---

## Fix 2: Parameterize All Colors

Replace every hardcoded color reference with the appropriate f-string variable.

### Primary Color (`{primary_color}`) — Replace `#1B365D`:

Search and replace these patterns in template.py:

```python
# Solid primary color usage
'#1B365D'  →  f'{primary_color}'

# Primary with alpha (hex+alpha notation for subtle tints)
'#1B365D08'  →  f'{primary_color}08'    # agent footer bg (3% opacity)
'#1B365D0A'  →  f'{primary_color}0A'    # CTA area bg (4% opacity)
'#1B365D0D'  →  f'{primary_color}0D'    # badge backgrounds (5% opacity)
'#1B365D0F'  →  f'{primary_color}0F'    # hero stat bg (6% opacity)
'#1B365D12'  →  f'{primary_color}12'    # badge bg variant (7% opacity)
'#1B365D15'  →  f'{primary_color}15'    # subtle borders (8% opacity)
'#1B365D1A'  →  f'{primary_color}1A'    # border variant (10% opacity)
'#1B365D26'  →  f'{primary_color}26'    # pill button borders (15% opacity)
'#1B365D33'  →  f'{primary_color}33'    # agent photo border (20% opacity)
'#1B365D40'  →  f'{primary_color}40'    # insight left border (25% opacity)
'#1B365DB3'  →  f'{primary_color}B3'    # hero label color (70% opacity)
```

### Accent Color (`{accent_color}`) — Replace `#B8860B`:

```python
'#B8860B'    →  f'{accent_color}'
'#B8860B0F'  →  f'{accent_color}0F'     # quick take bg
'#B8860B33'  →  f'{accent_color}33'     # quick take border
```

### Colors That Stay Hardcoded (DO NOT parameterize):

```python
# These are universal UI colors, not brand colors:
'#ffffff'   # White backgrounds
'#1c1917'   # Primary text (near black)
'#44403c'   # Secondary text
'#57534e'   # Tertiary text
'#78716c'   # Muted text / labels
'#a8a29e'   # Very muted text
'#9ca3af'   # Footer text
'#e7e5e4'   # Borders
'#e5e7eb'   # Dividers
'#f0efed'   # Outer email background
'#fafaf9'   # Subtle background (alternating rows, footer)
'#f5f5f4'   # Photo placeholder fallback
'#059669'   # Green (positive trends)
'#dc2626'   # Red (negative trends)
```

---

## Fix 3: Gradient References

The header gradient and accent strip also need parameterizing:

```python
# Header gradient
# BEFORE:
'background: linear-gradient(135deg, #1B365D 0%, #B8860B 100%)'
# AFTER:
f'background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%)'

# Accent strip
# BEFORE:
'background: linear-gradient(90deg, #1B365D 0%, #B8860B 100%)'
# AFTER:
f'background: linear-gradient(90deg, {primary_color} 0%, {accent_color} 100%)'

# Outlook VML gradient fallback
# BEFORE:
'<v:fill type="gradient" color="#1B365D" color2="#B8860B" angle="135"/>'
# AFTER:
f'<v:fill type="gradient" color="{primary_color}" color2="{accent_color}" angle="135"/>'

# Outlook VML CTA button fill
# BEFORE:
'fillcolor="#1B365D"'
# AFTER:
f'fillcolor="{primary_color}"'
```

---

## Fix 4: Branded Divider Gradient

The single-stacked layout uses a gradient divider between cards:

```python
# BEFORE:
'background: linear-gradient(90deg, #1B365D, #B8860B)'
# AFTER:
f'background: linear-gradient(90deg, {primary_color}, {accent_color})'
```

---

## Verification

After making changes, search template.py to confirm:

```bash
# Should return 0 results (no hardcoded brand colors left):
grep -c '#1B365D' template.py
grep -c '#B8860B' template.py

# Should return many results (parameterized):
grep -c 'primary_color' template.py
grep -c 'accent_color' template.py

# Body background should be #f0efed or #ffffff, never #f5f5f4 on the body tag:
grep 'body style' template.py
```

Then generate test HTML with two different color schemes to verify:

```python
# Test 1: Navy + Gold (default)
html1 = schedule_email_html(primary_color="#1B365D", accent_color="#B8860B", ...)

# Test 2: Forest Green + Copper (different brand)
html2 = schedule_email_html(primary_color="#2D5F3F", accent_color="#B87333", ...)

# Test 3: Deep Purple + Teal (different brand)
html3 = schedule_email_html(primary_color="#4A2D7A", accent_color="#2A9D8F", ...)
```

Open all three in Chrome. Each should look like a completely different brand — same layout, different personality. The body should be white in all three.
