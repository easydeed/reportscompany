# Template Integration Plan

## Summary
Integrating 3 new report templates that use JavaScript rendering with embedded data.

## Templates
1. **pct-open-houses-by-city.html** - Open Houses grouped by city
2. **pct-closed-by-city.html** - Closed sales grouped by city  
3. **pct-inventory-by-city.html** - Active inventory grouped by city

## Placeholders Needed

### Open Houses By City
- Header: `{{market_name}}`, `{{period_label}}`, `{{report_date}}`
- KPIs: `{{oh_this_week}}`, `{{oh_median_list}}`, `{{oh_new_added}}`, `{{oh_weekend_coverage}}`
- Trend: `{{oh_wow}}`, `{{oh_avg_8w}}`
- Data: `window.DATA = [...]` with city-level open house data

### Closed By City  
- Header: `{{market_name}}`, `{{period_label}}`, `{{report_date}}`
- KPIs: `{{total_closed}}`, `{{median_price}}`, `{{avg_dom}}`, `{{ctl}}`
- Trend: `{{compare_period}}`, `{{closed_mom}}`, `{{closed_yoy}}`
- Data: `window.DATA = [...]` with city-level closed sales data

### Inventory By City
- Header: `{{market_name}}`, `{{period_label}}`, `{{report_date}}`
- KPIs: `{{total_active}}`, `{{new_this_month}}`, `{{median_dom}}`, `{{moi}}`
- Trend: `{{compare_period}}`, `{{active_mom}}`, `{{active_yoy}}`
- Data: `window.DATA = [...]` with city-level inventory data

## Implementation Steps
1. ✅ Update print margins to 0.2in (DONE)
2. Add rendering functions to market_worker.py
3. Hook into existing profile_* functions
4. Enable PDF generation
5. Test all 3 report types

## Data Aggregation Logic

### For each template, group by city:
- Count properties per city
- Calculate median prices
- Calculate median DOM
- Calculate percentages/ratios
- Sort by count (descending)
- Take top 10-12 cities

## Status
- Print margins: ✅ DONE
- Rendering functions: IN PROGRESS

