# V0 → Jinja2 Translation Guide for Property Report Templates

## For: Cursor AI Implementation
## Reference: V0 design at `/v0-design/components/report/`
## Target: `apps/worker/src/worker/templates/property/`

---

## Overview

This guide translates the V0 React/Tailwind component designs into changes for our existing Jinja2 + CSS template system. The V0 output uses inline styles and per-theme conditionals — we need to map those back to our architecture: **base.jinja2** (shared HTML structure), **_macros.jinja2** (reusable components), and **5 theme files** (CSS overrides only).

**Architecture rule:** Theme files contain ONLY `<style>` blocks and `{% block cover %}` overrides. All other HTML structure lives in base.jinja2 and _macros.jinja2.

---

## CHANGE 1: Comp Card Photos (Critical — Biggest Visual Impact)

### Problem
Comp cards use `comp.map_image_url` (a Google Maps satellite thumbnail) at 100px tall. V0 uses proper property photos at 150px.

### File: `_macros.jinja2` — Update `comp_card` macro

**Current (line 209-245):**
```jinja2
{% macro comp_card(comp, index=1) %}
<div class="comp-card">
  <div class="comp-card-header">
    <span class="comp-number">{{ index }}</span>
    <span class="comp-price">{{ comp.sale_price | format_currency }}</span>
  </div>
  {% if comp.map_image_url %}
  <div class="comp-image">
    <img src="{{ comp.map_image_url }}" alt="{{ comp.address }}">
  </div>
  {% endif %}
  ...
```

**Replace with:**
```jinja2
{% macro comp_card(comp, index=1) %}
<div class="comp-card">
  {# Photo FIRST, then header — matches V0 design: image on top, header bar below #}
  {% if comp.photo_url or comp.map_image_url %}
  <div class="comp-image">
    <img src="{{ comp.photo_url | default(comp.map_image_url) }}" alt="{{ comp.address }}">
  </div>
  {% endif %}
  <div class="comp-card-header">
    <span class="comp-number">{{ index }}</span>
    <span class="comp-price">{{ comp.sale_price | format_currency }}</span>
  </div>
  ...
```

**Key changes:**
1. **Image ABOVE header** (V0 has photo → price bar → details, not price bar → photo → details)
2. **Prefer `comp.photo_url`** over `comp.map_image_url` — falls back to map if no photo
3. Photo URL must be populated by `property_builder.py` (see Change 8 below)

### File: `base.jinja2` — Update `.comp-image` CSS

**Current CSS (find in base.jinja2 style block):**
```css
.comp-image {
  height: 100px;
  overflow: hidden;
}
```

**Replace with:**
```css
.comp-image {
  height: 150px;
  overflow: hidden;
}

.comp-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

### File: Each theme file — Update `.comp-image` height if overridden
Some themes override `.comp-image` height. Remove those overrides so the base 150px applies universally, or set theme-specific heights.

---

## CHANGE 2: Aerial Page — Add Property Marker + Info Bar

### Problem
Aerial page is just a map in a box. V0 adds a property marker overlay and an info bar below the map.

### File: `_macros.jinja2` — Update `map_card` macro

**Add a new macro for the aerial info bar:**
```jinja2
{# Aerial page info bar below map #}
{% macro aerial_info_bar(property) %}
<div class="aerial-info-bar">
  <div class="aerial-info-item">
    <span class="aerial-info-label">Neighborhood</span>
    <span class="aerial-info-value">{{ property.neighborhood | default(property.city) }}</span>
  </div>
  <div class="aerial-info-divider"></div>
  <div class="aerial-info-item">
    <span class="aerial-info-label">Coordinates</span>
    <span class="aerial-info-value">{{ property.latitude }}, {{ property.longitude }}</span>
  </div>
  <div class="aerial-info-divider"></div>
  <div class="aerial-info-item">
    <span class="aerial-info-label">ZIP Code</span>
    <span class="aerial-info-value">{{ property.zip_code }}</span>
  </div>
  <div class="aerial-info-divider"></div>
  <div class="aerial-info-item">
    <span class="aerial-info-label">County</span>
    <span class="aerial-info-value">{{ property.county | default('—') }}</span>
  </div>
</div>
{% endmacro %}
```

### File: `_macros.jinja2` — Update `map_card` macro to include property marker overlay

**Replace existing `map_card` (line 324-337):**
```jinja2
{% macro map_card(image_url, title=None, property=None) %}
<div class="map-card">
  {% if title %}
  <div class="map-card-header">{{ title }}</div>
  {% endif %}
  <div class="map-card-image">
    {% if image_url %}
    <img src="{{ image_url }}" alt="{{ title | default('Map') }}">
    {# Property marker overlay #}
    {% if property %}
    <div class="map-marker">
      <span class="map-marker-label">{{ property.street_address }}</span>
      <svg class="map-marker-pin" width="12" height="16" viewBox="0 0 12 16">
        <path d="M6 0C2.7 0 0 2.7 0 6c0 4.5 6 10 6 10s6-5.5 6-10c0-3.3-2.7-6-6-6z" fill="var(--color-accent)"/>
        <circle cx="6" cy="6" r="2.5" fill="white"/>
      </svg>
    </div>
    {% endif %}
    {% else %}
    <div class="map-placeholder">Map not available</div>
    {% endif %}
  </div>
</div>
{% endmacro %}
```

### File: `base.jinja2` — Update aerial page block

**Current (line 811-818):**
```jinja2
{% block aerial %}
<div class="page-content">
  {{ macros.page_header('Aerial View', property.full_address) }}
  {{ macros.map_card(images.aerial_map, 'Property Location') }}
</div>
{{ macros.page_footer(agent, 3) }}
{% endblock %}
```

**Replace with:**
```jinja2
{% block aerial %}
<div class="page-content">
  {{ macros.page_header('Aerial View', property.full_address) }}
  {{ macros.map_card(images.aerial_map, 'Property Location', property) }}
  {{ macros.aerial_info_bar(property) }}
</div>
{{ macros.page_footer(agent, 3) }}
{% endblock %}
```

### File: `base.jinja2` — Add CSS for marker and info bar

```css
/* Aerial map marker overlay */
.map-card-image {
  position: relative;
}

.map-marker {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -100%);
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.map-marker-label {
  font-family: var(--font-body);
  font-size: 9px;
  font-weight: 700;
  color: white;
  background: var(--color-accent);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  white-space: nowrap;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.map-marker-pin {
  margin-top: -1px;
}

/* Aerial info bar */
.aerial-info-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding: 12px 16px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.aerial-info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.aerial-info-label {
  font-family: var(--font-body);
  font-size: 8px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 2px;
}

.aerial-info-value {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
}

.aerial-info-divider {
  width: 1px;
  height: 24px;
  background: var(--color-border);
}
```

---

## CHANGE 3: Property Details Page — Add Key Stats Bar

### Problem
V0 adds a prominent colored stats bar at the top of the details page (Beds/Baths/SqFt/Year on a primary-colored background). Currently missing.

### File: `_macros.jinja2` — Add new macro

```jinja2
{# Key stats highlight bar for property details page #}
{% macro property_key_stats_bar(property) %}
<div class="key-stats-bar">
  <div class="key-stat-item">
    <span class="key-stat-value">{{ property.bedrooms }}</span>
    <span class="key-stat-label">Beds</span>
  </div>
  <div class="key-stat-divider"></div>
  <div class="key-stat-item">
    <span class="key-stat-value">{{ property.bathrooms }}</span>
    <span class="key-stat-label">Baths</span>
  </div>
  <div class="key-stat-divider"></div>
  <div class="key-stat-item">
    <span class="key-stat-value">{{ property.sqft | format_number }}</span>
    <span class="key-stat-label">Sq Ft</span>
  </div>
  <div class="key-stat-divider"></div>
  <div class="key-stat-item">
    <span class="key-stat-value">{{ property.year_built }}</span>
    <span class="key-stat-label">Year Built</span>
  </div>
</div>
{% endmacro %}
```

### File: `base.jinja2` — Insert into property details page block

**Current (line 824-841):**
```jinja2
{% block property_details %}
<div class="page-content">
  {{ macros.page_header('Property Details', property.full_address) }}
  <div class="two-column">
```

**Replace with:**
```jinja2
{% block property_details %}
<div class="page-content">
  {{ macros.page_header('Property Details', property.full_address) }}
  {{ macros.property_key_stats_bar(property) }}
  <div class="two-column">
```

### File: `base.jinja2` — Add CSS

```css
/* Key stats bar */
.key-stats-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  margin-bottom: 18px;
  background: var(--color-primary);
  border-radius: var(--radius-lg);
}

.key-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.key-stat-value {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: white;
  line-height: 1;
}

.key-stat-label {
  font-family: var(--font-body);
  font-size: 8px;
  color: rgba(255,255,255,0.6);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 2px;
}

.key-stat-divider {
  width: 1px;
  height: 28px;
  background: rgba(255,255,255,0.15);
}
```

### File: `teal.jinja2` — Override stat value color for teal theme
```css
.key-stat-value {
  color: var(--color-primary);
}
.key-stat-label {
  color: rgba(52,209,195,0.7);
}
```

---

## CHANGE 4: Analysis Page — Add Comparison Table + Price Position Bar

### Problem
Analysis page currently only has the `analysis_summary` macro. V0 adds a Subject vs Comp Average comparison table with green/red indicators, and a price position bar.

### File: `_macros.jinja2` — Add new macros

```jinja2
{# Subject vs Comp Average comparison table #}
{% macro comparison_table(stats, property) %}
<div class="comparison-section">
  <h3 class="section-title">Subject Property vs. Comparable Averages</h3>
  <div class="comparison-table">
    <div class="comparison-header">
      <span>Metric</span>
      <span>Subject Property</span>
      <span>Comp Average</span>
      <span>Difference</span>
    </div>
    {% set rows = [
      {'metric': 'Price', 'subject': stats.piq.price | format_currency, 'comp': stats.medium.price | format_currency, 'diff': stats.piq.price - stats.medium.price, 'is_currency': true},
      {'metric': 'Sq Ft', 'subject': property.sqft | format_number, 'comp': stats.avg_sqft | format_number, 'diff': property.sqft - stats.avg_sqft, 'is_currency': false},
      {'metric': 'Beds', 'subject': property.bedrooms, 'comp': stats.avg_beds, 'diff': property.bedrooms - stats.avg_beds, 'is_currency': false},
      {'metric': 'Baths', 'subject': property.bathrooms, 'comp': stats.avg_baths, 'diff': property.bathrooms - stats.avg_baths, 'is_currency': false},
      {'metric': '$/Sq Ft', 'subject': stats.piq.price_per_sqft | format_currency, 'comp': stats.avg_price_per_sqft | format_currency, 'diff': stats.piq.price_per_sqft - stats.avg_price_per_sqft, 'is_currency': true}
    ] %}
    {% for row in rows %}
    <div class="comparison-row {% if loop.index is odd %}comparison-row-stripe{% endif %}">
      <span class="comparison-metric">{{ row.metric }}</span>
      <span class="comparison-subject">{{ row.subject }}</span>
      <span class="comparison-comp">{{ row.comp }}</span>
      <span class="comparison-diff {% if row.diff >= 0 %}diff-positive{% else %}diff-negative{% endif %}">
        {% if row.is_currency %}{{ row.diff | abs | format_currency }}{% else %}{{ row.diff | abs }}{% endif %}
        {% if row.diff >= 0 %}+{% else %}-{% endif %}
      </span>
    </div>
    {% endfor %}
  </div>
</div>
{% endmacro %}

{# Price position bar showing subject property in range #}
{% macro price_position_bar(stats) %}
{% set low = stats.price_low %}
{% set high = stats.price_high %}
{% set subject = stats.piq.price | default(stats.medium.price) %}
{% set range = high - low %}
{% set position = ((subject - low) / range * 100) | int %}
<div class="price-position-section">
  <div class="price-position-label">Subject property position in price range</div>
  <div class="price-position-container">
    <div class="price-position-track">
      <div class="price-position-marker" style="left: {{ position }}%">
        <span class="price-position-value">{{ subject | format_currency }}</span>
        <span class="price-position-tick"></span>
      </div>
    </div>
    <div class="price-position-range-labels">
      <span>{{ low | format_currency }}</span>
      <span>{{ high | format_currency }}</span>
    </div>
  </div>
</div>
{% endmacro %}
```

### File: `base.jinja2` — Update analysis page block

**Current (line 847-855):**
```jinja2
{% block analysis %}
<div class="page-content">
  {{ macros.page_header('Area Sales Analysis', 'Comparable Sales Summary') }}
  {{ macros.analysis_summary(stats, property) }}
</div>
{{ macros.page_footer(agent, 5) }}
{% endblock %}
```

**Replace with:**
```jinja2
{% block analysis %}
<div class="page-content">
  {{ macros.page_header('Area Sales Analysis', 'Comparable market statistics and pricing') }}
  {{ macros.analysis_summary(stats, property) }}
  {{ macros.price_position_bar(stats) }}
  {{ macros.comparison_table(stats, property) }}
</div>
{{ macros.page_footer(agent, 5) }}
{% endblock %}
```

### File: `base.jinja2` — Add CSS

```css
/* Comparison table */
.comparison-section { margin-top: 16px; }

.section-title {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.comparison-table {
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.comparison-header {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  padding: 8px 12px;
  background: var(--color-primary);
  font-family: var(--font-body);
  font-size: 9px;
  font-weight: 700;
  color: white;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.comparison-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  padding: 7px 12px;
  font-size: 10px;
}

.comparison-row-stripe {
  background: var(--color-surface);
}

.comparison-metric {
  font-family: var(--font-body);
  font-weight: 600;
  color: var(--color-primary);
}

.comparison-subject {
  font-family: var(--font-body);
  color: var(--color-text);
}

.comparison-comp {
  font-family: var(--font-body);
  color: var(--color-text-muted);
}

.comparison-diff {
  font-family: var(--font-body);
  font-weight: 700;
}

.diff-positive { color: #16A34A; }
.diff-negative { color: #DC2626; }

/* Price position bar */
.price-position-section { margin-top: 4px; }

.price-position-label {
  font-family: var(--font-body);
  font-size: 9px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
}

.price-position-container {
  position: relative;
  height: 36px;
}

.price-position-track {
  position: absolute;
  top: 12px;
  left: 0;
  right: 0;
  height: 12px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-border) 0%, var(--color-accent) 100%);
}

.price-position-marker {
  position: absolute;
  top: -12px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.price-position-value {
  font-family: var(--font-body);
  font-size: 8px;
  font-weight: 700;
  color: var(--color-primary);
  white-space: nowrap;
  margin-bottom: 1px;
}

.price-position-tick {
  display: block;
  width: 3px;
  height: 24px;
  background: var(--color-primary);
  border-radius: 2px;
}

.price-position-range-labels {
  position: absolute;
  bottom: -14px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  font-family: var(--font-body);
  font-size: 8px;
  color: var(--color-text-muted);
}
```

---

## CHANGE 5: Range Page — Add Stats Grid, Market Insight, Comp Position Bars

### Problem
Range page is currently just a thin gradient bar + flat address list. V0 adds summary stats, a market insight section, comp position dots on the bar, and mini progress bars per comp.

### File: `base.jinja2` — Replace range page block

**Replace current range block (line 872-889) with:**
```jinja2
{% block range %}
<div class="page-content">
  {{ macros.page_header('Range of Sales', 'Price positioning and market insight') }}

  {# Visual Price Range Bar with comp markers #}
  <div class="range-bar-container">
    <div class="range-bar-label">Estimated Value Position</div>
    <div class="range-bar-visual">
      <div class="range-bar-track">
        {# Comp dot markers #}
        {% for comp in comparables[:4] %}
        {% set pct = ((comp.sale_price - stats.price_low) / (stats.price_high - stats.price_low) * 100) | int %}
        <div class="range-bar-dot" style="left: {{ pct }}%"></div>
        {% endfor %}
        {# Subject marker #}
        {% set subject_pct = ((stats.piq.price - stats.price_low) / (stats.price_high - stats.price_low) * 100) | int %}
        <div class="range-bar-subject" style="left: {{ subject_pct }}%">
          <span class="range-bar-subject-label">{{ stats.piq.price | format_currency }}</span>
          <span class="range-bar-subject-arrow"></span>
        </div>
      </div>
      <div class="range-bar-endpoints">
        <span>{{ stats.price_low | format_currency }}</span>
        <span>{{ stats.price_high | format_currency }}</span>
      </div>
    </div>
  </div>

  {# Comparable Sales Summary with mini position bars #}
  <div class="range-comps-section">
    <h3 class="section-title">Comparable Sales Summary</h3>
    <div class="range-comps-list">
      {% for comp in comparables[:4] | sort(attribute='sale_price') %}
      {% set pct = ((comp.sale_price - stats.price_low) / (stats.price_high - stats.price_low) * 100) | int %}
      <div class="range-comp-item">
        <span class="range-comp-dot"></span>
        <span class="range-comp-address">{{ comp.address }}</span>
        <span class="range-comp-distance">{{ comp.distance_miles }} mi</span>
        <span class="range-comp-price">{{ comp.sale_price | format_currency }}</span>
        <div class="range-comp-minibar">
          <div class="range-comp-minibar-fill" style="width: {{ pct }}%"></div>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>

  {# Summary Statistics Grid #}
  <div class="range-stats-grid">
    <div class="range-stat-card">
      <span class="range-stat-value">{{ stats.avg_price_per_sqft | format_currency }}</span>
      <span class="range-stat-label">Avg $/Sq Ft</span>
    </div>
    <div class="range-stat-card">
      <span class="range-stat-value">{{ stats.avg_days_on_market | default('—') }}</span>
      <span class="range-stat-label">Avg Days on Market</span>
    </div>
    <div class="range-stat-card">
      <span class="range-stat-value">{{ stats.active_listings | default('—') }}</span>
      <span class="range-stat-label">Active Listings</span>
    </div>
    <div class="range-stat-card">
      <span class="range-stat-value">{{ stats.total_comps }}</span>
      <span class="range-stat-label">Comparables</span>
    </div>
  </div>

  {# Market Insight #}
  <div class="market-insight">
    <h4 class="market-insight-title">Market Insight</h4>
    <p class="market-insight-text">
      Based on {{ stats.total_comps }} comparable sales within {{ stats.max_distance | default('1') }} miles, the estimated market value for this property falls between {{ stats.price_low | format_currency }} and {{ stats.price_high | format_currency }}. The median comparable sold at {{ stats.medium.price | format_currency }}, suggesting strong market positioning.
    </p>
  </div>
</div>
{{ macros.page_footer(agent, 7) }}
{% endblock %}
```

### File: `base.jinja2` — Add CSS for new range page elements

```css
/* Range bar container */
.range-bar-container {
  padding: 20px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  margin-bottom: 16px;
}

.range-bar-label {
  font-family: var(--font-body);
  font-size: 9px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 20px;
}

.range-bar-visual {
  position: relative;
  height: 56px;
  margin-bottom: 8px;
}

.range-bar-track {
  position: absolute;
  top: 26px;
  left: 0;
  right: 0;
  height: 16px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-border) 0%, var(--color-accent) 100%);
}

.range-bar-dot {
  position: absolute;
  top: 3px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: white;
  border: 2px solid var(--color-primary);
  transform: translateX(-50%);
  z-index: 2;
}

.range-bar-subject {
  position: absolute;
  top: -26px;
  transform: translateX(-50%);
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.range-bar-subject-label {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  color: var(--color-accent);
  white-space: nowrap;
  margin-bottom: 2px;
}

.range-bar-subject-arrow {
  display: block;
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 8px solid var(--color-accent);
}

.range-bar-endpoints {
  position: absolute;
  bottom: -4px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  font-family: var(--font-body);
  font-size: 9px;
  color: var(--color-text-muted);
}

/* Range comps with mini bars */
.range-comps-section { margin-bottom: 16px; }

.range-comp-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
}

.range-comp-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-accent);
  flex-shrink: 0;
}

.range-comp-address {
  flex: 1;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 600;
  color: var(--color-primary);
}

.range-comp-distance {
  font-family: var(--font-body);
  font-size: 9px;
  color: var(--color-text-muted);
  min-width: 50px;
  text-align: center;
}

.range-comp-price {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  min-width: 90px;
  text-align: right;
}

.range-comp-minibar {
  position: relative;
  width: 60px;
  height: 6px;
  background: var(--color-border);
  border-radius: 3px;
  flex-shrink: 0;
}

.range-comp-minibar-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: 3px;
  background: var(--color-accent);
  opacity: 0.7;
}

/* Range stats grid */
.range-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.range-stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px 6px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.range-stat-value {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
}

.range-stat-label {
  font-family: var(--font-body);
  font-size: 7px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 3px;
  text-align: center;
}

/* Market insight */
.market-insight {
  padding: 14px 16px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.market-insight-title {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0 0 6px 0;
}

.market-insight-text {
  font-family: var(--font-body);
  font-size: 10px;
  color: var(--color-text-muted);
  line-height: 1.6;
  margin: 0;
}
```

---

## CHANGE 6: TOC Page — Add Sidebar Accent

### Problem
V0 adds a thin vertical accent bar on the left side of the contents page.

### File: `base.jinja2` — Update contents page structure

**Current (line ~786-805):**
```jinja2
{% block contents %}
<div class="page-content">
  {{ macros.page_header('Contents', 'Property Report Overview') }}
  <div class="contents-list">
```

**Replace with:**
```jinja2
{% block contents %}
<div class="page-content contents-layout">
  <div class="contents-sidebar-accent"></div>
  <div class="contents-main">
    {{ macros.page_header('Contents', 'Property Report Overview') }}
    <div class="contents-list">
```

And close the extra div before the footer.

### File: `base.jinja2` — Add CSS
```css
.contents-layout {
  display: flex;
}

.contents-sidebar-accent {
  width: 3px;
  background: var(--color-accent);
  margin-right: 24px;
  opacity: 0.4;
  border-radius: 2px;
}

.contents-main {
  flex: 1;
}
```

---

## CHANGE 7: Theme-Specific Overrides

Each theme file should add overrides for the new elements. Here are the key per-theme additions:

### `bold.jinja2` — Add to `{% block theme_styles %}`
```css
.section-title {
  text-transform: uppercase;
  letter-spacing: 1.5px;
}

.comparison-header {
  background: var(--color-primary);
}

.range-bar-track {
  background: linear-gradient(90deg, var(--color-surface) 0%, var(--color-accent) 100%);
}

.market-insight-title {
  text-transform: uppercase;
  letter-spacing: 1px;
}
```

### `elegant.jinja2` — Add to `{% block theme_styles %}`
```css
.section-title {
  font-style: italic;
  font-weight: 500;
  letter-spacing: 0;
}

.comparison-table {
  border: none;
}

.comparison-header {
  background: transparent;
  color: var(--color-primary);
  border-bottom: 2px solid var(--color-accent);
}

.comparison-row {
  padding: 7px 0;
  border-bottom: 1px solid var(--color-border);
}

.comparison-row-stripe {
  background: transparent;
}

.aerial-info-value {
  font-style: italic;
}

.key-stat-value {
  font-style: italic;
}

.range-stat-value {
  font-style: italic;
}

.market-insight {
  background: transparent;
  border-left: 3px solid var(--color-accent);
}

.market-insight-title {
  font-style: italic;
}

.contents-sidebar-accent {
  display: none;
}
```

### `modern.jinja2` — Add to `{% block theme_styles %}`
```css
.range-bar-track {
  background: linear-gradient(90deg, var(--color-border) 0%, var(--color-primary) 100%);
  border-radius: 8px;
}

.range-comp-dot {
  background: var(--color-primary);
}

.range-comp-minibar-fill {
  background: var(--color-primary);
}

.range-bar-subject-label {
  color: var(--color-primary);
}

.range-bar-subject-arrow {
  border-top-color: var(--color-primary);
}

.contents-sidebar-accent {
  display: none;
}
```

### `teal.jinja2` — Add to `{% block theme_styles %}`
```css
.comparison-row:nth-child(odd) .comparison-row-stripe,
.comparison-row-stripe {
  background: var(--color-row-a);
}

.comparison-row:nth-child(even) {
  background: var(--color-row-b);
}

.range-bar-track {
  background: linear-gradient(90deg, var(--color-row-a) 0%, var(--color-primary) 50%, var(--color-row-b) 100%);
}

.range-comp-item:nth-child(odd) { background: var(--color-row-a); }
.range-comp-item:nth-child(even) { background: var(--color-row-b); }
```

---

## CHANGE 8: property_builder.py — Pass Photo URLs Through

### Problem
Comp cards need `photo_url` from SimplyRETS listings data. Currently only `map_image_url` (Google Maps satellite) is passed.

### File: `apps/worker/src/worker/property_builder.py`

In the method that builds the comparables list for template context, ensure each comp dict includes:

```python
{
    "photo_url": comp.get("photo_url") or comp.get("photos", [{}])[0].get("url", ""),
    "map_image_url": f"https://maps.googleapis.com/maps/api/staticmap?..."  # existing
}
```

The exact field name depends on what SimplyRETS returns. Check `normalize_comparable()` in `apps/api/src/api/schemas/property.py` for the field mapping.

**Also add to template context for range page new fields:**
```python
"stats": {
    ...existing fields...
    "avg_price_per_sqft": avg_price_per_sqft,  # Format: "$XXX"
    "avg_days_on_market": avg_dom or "—",
    "active_listings": active_count or "—",
    "max_distance": max_distance_miles,
}
```

---

## CHANGE 9: Cover Page — No Structural Changes Needed

The V0 cover page closely matches the existing theme cover overrides. The current cover implementations in all 5 theme files are already well-designed with unique decorative elements. **No changes needed** — the themes already have:

- Bold: Corner triangle, gold accent bar
- Classic: Two-tone accent bar, refined typography
- Elegant: Corner flourishes, italic display
- Modern: Decorative circles, pill shapes
- Teal: Diagonal stripe, mini bars

---

## Implementation Order (Recommended)

1. **Change 8** (property_builder.py) — Data pipeline first, so photos are available
2. **Change 1** (comp cards) — Biggest visual impact, simplest change
3. **Change 3** (details key stats bar) — Quick win, standalone
4. **Change 2** (aerial marker + info bar) — Medium complexity
5. **Change 4** (analysis comparison table) — New macros, moderate complexity
6. **Change 5** (range page overhaul) — Most complex, save for last
7. **Change 6** (TOC sidebar) — Small polish
8. **Change 7** (theme overrides) — Apply after base changes are working

---

## Testing Checklist

- [ ] Comp cards show property photos (not just satellite maps)
- [ ] Comp cards render at 150px photo height across all 5 themes
- [ ] Aerial page shows property marker label centered on map
- [ ] Aerial info bar displays below map on all themes
- [ ] Property details page has key stats bar at top
- [ ] Analysis page shows comparison table with green/red indicators
- [ ] Analysis page shows price position bar
- [ ] Range page shows enhanced bar with comp dots and subject arrow
- [ ] Range page shows stats grid (4 cards)
- [ ] Range page shows market insight text block
- [ ] PDF renders correctly in both Playwright (local) and PDFShift (production)
- [ ] Footer doesn't overlap with new content on any page
- [ ] All 5 themes render without visual bugs
