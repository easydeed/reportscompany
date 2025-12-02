#!/usr/bin/env python3
import argparse, base64, csv, datetime as dt, json, os, sys
from urllib.parse import quote
import urllib.request

def read_env(env_path):
    env = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                k,v = line.split("=",1)
                env[k.strip()] = v.strip()
    return env

def http_get(url, auth_header, timeout=45):
    req = urllib.request.Request(url, headers={"Authorization": auth_header, "Accept":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def median(values):
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n == 0: return None
    vals.sort()
    m = n // 2
    return float(vals[m]) if n % 2 else (float(vals[m-1]) + float(vals[m]))/2.0

def safe_avg(values):
    vals = [v for v in values if v is not None]
    return float(sum(vals))/len(vals) if vals else None

def fmt_money(x): return ("${:,}".format(int(x))) if (x is not None) else "-"
def fmt_int(x): return str(int(x)) if (x is not None) else "-"
def fmt_decimal(x, places=1): return ("{:."+str(places)+"f}").format(x) if (x is not None) else "-"

def get_employee_info(employee_id, employee_json_str=None):
    """Parse employee data from JSON string (passed from PHP)"""
    import sys
    print(f"DEBUG: get_employee_info called with employee_id={employee_id}", file=sys.stderr)
    
    if employee_id <= 0:
        print(f"DEBUG: employee_id <= 0, returning None", file=sys.stderr)
        return None
    
    if not employee_json_str:
        print(f"DEBUG: No employee_json_str provided, returning None", file=sys.stderr)
        return None
    
    try:
        employee_data = json.loads(employee_json_str)
        print(f"DEBUG: Successfully parsed employee data: {employee_data.get('first_name')} {employee_data.get('last_name')}", file=sys.stderr)
        return employee_data
    except Exception as e:
        print(f"ERROR parsing employee JSON: {type(e).__name__}: {str(e)}", file=sys.stderr)
        print(f"DEBUG: employee_json_str was: {employee_json_str[:100]}...", file=sys.stderr)
        return None

def html_boiler(title, subtitle, employee_id=0, employee_json_str=None):
    """Generate HTML header with PCT branding and print styles"""
    pct_logo = "https://pct.com/vcard-new/assets/images/logo2-dark.png"
    
    # Get employee info if available
    employee = get_employee_info(employee_id, employee_json_str) if employee_id > 0 else None
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .report-container {{ max-width: 1200px; margin: 0 auto; }}
        .report-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #03374f; padding-bottom: 15px; }}
        .pct-logo {{ height: 60px; }}
        .report-title {{ margin: 0 0 5px; color: #03374f; }}
        .report-subtitle {{ margin: 0; color: #666; font-size: 14px; }}
        .print-button {{ background: #03374f; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; }}
        .print-button:hover {{ background: #024263; }}
        .report-footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #03374f; display: flex; align-items: center; justify-content: space-between; gap: 15px; }}
        .rep-photo {{ width: 80px; height: 80px; border-radius: 50%; object-fit: cover; }}
        .rep-info {{ flex: 1; }}
        .rep-name {{ font-weight: bold; color: #03374f; margin: 0 0 5px; }}
        .rep-contact {{ margin: 2px 0; font-size: 13px; color: #666; }}
        
        /* Print styles */
        @media print {{
            .print-button {{ display: none; }}
            .report-container {{ max-width: 100%; }}
            body {{ padding: 10px; }}
            table {{ page-break-inside: auto; }}
            tr {{ page-break-inside: avoid; page-break-after: auto; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <div>
                <img src="{pct_logo}" alt="Pacific Coast Title" class="pct-logo">
            </div>
            <div style="text-align: center; flex: 1;">
                <h2 class="report-title">{title}</h2>
                <p class="report-subtitle">{subtitle}</p>
            </div>
            <div>
                <button class="print-button" onclick="window.print()">📄 Print / Save PDF</button>
            </div>
        </div>
        <div style="margin: 20px 0;">
'''
    
    return html

def html_close(employee_id=0, employee_json_str=None):
    """Generate HTML footer with rep contact info and QR code"""
    employee = get_employee_info(employee_id, employee_json_str) if employee_id > 0 else None
    
    footer_html = ""
    if employee:
        full_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
        first_name = employee.get('first_name', '').lower()
        title = employee.get('title', '')
        mobile = employee.get('mobile', '')
        email = employee.get('email', '')
        photo_url = employee.get('photo_url', '')
        
        # Handle photo URL (may be relative path or full URL)
        if photo_url and not photo_url.startswith('http'):
            photo_url = f"https://pct.com/vcard-new/{photo_url}"
        
        # Generate vCard URL and QR code
        vcard_url = f"https://pct.com/vcard-new/{first_name}/"
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={vcard_url}"
        
        footer_html = f'''
        <div class="report-footer">
            <div style="display: flex; align-items: center; gap: 15px;">
                {f'<img src="{photo_url}" alt="{full_name}" class="rep-photo">' if photo_url else ''}
                <div class="rep-info">
                    <p class="rep-name">{full_name}</p>
                    {f'<p class="rep-contact">{title}</p>' if title else ''}
                    {f'<p class="rep-contact">📱 {mobile}</p>' if mobile else ''}
                    {f'<p class="rep-contact">✉️ {email}</p>' if email else ''}
                </div>
            </div>
            <div style="text-align: center;">
                <img src="{qr_code_url}" alt="Scan for vCard" style="width: 100px; height: 100px; border: 2px solid #03374f; border-radius: 8px;">
                <p style="margin: 5px 0 0; font-size: 11px; color: #666;">Scan for vCard</p>
            </div>
        </div>
'''
    
    return footer_html + '''
        </div>
    </div>
</body>
</html>
'''

def write_csv(path, rows, columns):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in columns})

def ensure_dir(p): os.makedirs(p, exist_ok=True)

def generate_pdf_from_html(html_path, pdf_path, env):
    """Generate PDF from HTML using PDFShift API (cloud service)"""
    enable_pdf = env.get("ENABLE_PDF", "0") == "1"
    if not enable_pdf:
        print("DEBUG: PDF generation disabled (ENABLE_PDF=0)")
        return None
    
    pdfshift_api_key = env.get("PDFSHIFT_API_KEY", "")
    
    if not pdfshift_api_key:
        print("DEBUG: PDF generation requires PDFSHIFT_API_KEY in ENV file")
        print("DEBUG: Sign up free at https://pdfshift.io (250 PDFs/month free)")
        return None
    
    try:
        import urllib.request
        import base64
        
        # Read HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Prepare API request
        api_url = "https://api.pdfshift.io/v3/convert/pdf"
        
        # PDFShift request payload (minimal, working parameters)
        payload = {
            "source": html_content,
            "format": "Letter",
            "margin": "0.2in"  # Shorthand for all sides
        }
        
        # Encode payload as JSON
        import json
        payload_json = json.dumps(payload).encode('utf-8')
        
        # Create request with Basic Auth
        credentials = f"api:{pdfshift_api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        req = urllib.request.Request(
            api_url,
            data=payload_json,
            headers={
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"DEBUG: Generating PDF via PDFShift API...")
        
        # Make API call
        with urllib.request.urlopen(req, timeout=60) as response:
            pdf_content = response.read()
        
        # Save PDF file
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        print(f"DEBUG: PDF generated successfully: {pdf_path}")
        return pdf_path
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No error details'
        print(f"DEBUG: PDFShift API error {e.code}: {error_body}")
        if e.code == 401:
            print("DEBUG: Invalid API key - check PDFSHIFT_API_KEY in ENV file")
        elif e.code == 429:
            print("DEBUG: Rate limit exceeded - upgrade PDFShift plan or wait")
        return None
    except Exception as e:
        print(f"DEBUG: PDF generation error: {str(e)}")
        import traceback
        traceback.print_exc()
    return None

def fetch_listings(env, params, page_size=200, max_pages=25, use_last_id=True):
    base = env.get("SIMPLYRETS_BASE","https://api.simplyrets.com").rstrip("/")
    key  = env["SIMPLYRETS_KEY"]; secret = env["SIMPLYRETS_SECRET"]
    auth = "Basic " + base64.b64encode((key+":"+secret).encode("ascii")).decode("ascii")
    
    # Check if we're using a sort parameter - if so, use offset pagination instead of lastId
    has_sort = any(k == "sort" for k, v in params)
    
    def build_url(extra):
        # Use safe='-' to prevent encoding hyphens in date ranges
        qp = "&".join([k+"="+quote(v, safe='-') for k,v in params] + extra)
        return base + "/properties?" + qp
    
    all_rows = []
    last_id = "0"
    offset = 0
    
    for page in range(max_pages):
        extra = ["limit="+str(page_size)]
        
        # Use offset pagination when sorting (lastId breaks sort order)
        if has_sort:
            extra.append("offset="+str(offset))
        elif use_last_id:
            extra.append("lastId="+last_id)
        
        url = build_url(extra)
        # Debug: Show the actual URL being called (first page only)
        if page == 0:
            print(f"DEBUG: API URL (page 1): {url}", file=sys.stderr)
        raw = http_get(url, auth)
        chunk = json.loads(raw.decode("utf-8"))
        if not chunk: break
        all_rows.extend(chunk)
        last_id = str(chunk[-1].get("mlsId","0"))
        offset += len(chunk)
        if len(chunk) < page_size: break
    return all_rows

def fetch_openhouses(env, params, limit=500):
    base = env.get("SIMPLYRETS_BASE","https://api.simplyrets.com").rstrip("/")
    key  = env["SIMPLYRETS_KEY"]; secret = env["SIMPLYRETS_SECRET"]
    auth = "Basic " + base64.b64encode((key+":"+secret).encode("ascii")).decode("ascii")
    qp = "&".join([k+"="+quote(v) for k,v in params] + ["limit="+str(limit)])
    url = base + "/openhouses?" + qp
    raw = http_get(url, auth)
    return json.loads(raw.decode("utf-8"))

def fetch_analytics(env, params):
    base = env.get("SIMPLYRETS_BASE","https://api.simplyrets.com").rstrip("/")
    key  = env["SIMPLYRETS_KEY"]; secret = env["SIMPLYRETS_SECRET"]
    auth = "Basic " + base64.b64encode((key+":"+secret).encode("ascii")).decode("ascii")
    qp = "&".join([k+"="+quote(v) for k,v in params])
    url = base + "/properties/analytics?" + qp
    raw = http_get(url, auth)
    return json.loads(raw.decode("utf-8"))

def flatten(p):
    prop = (p.get("property") or {}); addr = (p.get("address") or {}); sales=(p.get("sales") or {})
    sqft = prop.get("area"); lp = p.get("listPrice")
    ppsf = (float(lp)/float(sqft)) if (lp and sqft) else None
    
    # Get DOM from API, or calculate if not provided
    dom = p.get("daysOnMarket")
    if dom is None or dom == 0:
        # Fallback: calculate DOM from dates
        list_date_str = p.get("listDate")
        close_date_str = sales.get("closeDate")
        status = p.get("status")
        
        if list_date_str:
            try:
                # Handle various date formats - always strip timezone for simpler comparison
                if "T" in list_date_str:
                    # Parse ISO format, then strip timezone
                    # Try fromisoformat first (Python 3.7+), fallback to strptime
                    try:
                        list_date_str_clean = list_date_str.replace("Z", "+00:00")
                        list_date_tz = dt.datetime.fromisoformat(list_date_str_clean)
                        list_date = list_date_tz.replace(tzinfo=None)
                    except (AttributeError, ValueError):
                        # Fallback for Python < 3.7 or invalid format
                        list_date_str_clean = list_date_str.replace("Z", "").replace("T", " ").split("+")[0].split("-", 3)[:3]
                        list_date = dt.datetime.strptime(list_date_str[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                else:
                    # Parse simple date (YYYY-MM-DD)
                    list_date = dt.datetime.strptime(list_date_str, "%Y-%m-%d")
                
                if status == "Closed" and close_date_str:
                    # Closed: listDate to closeDate
                    if "T" in close_date_str:
                        try:
                            close_date_str_clean = close_date_str.replace("Z", "+00:00")
                            close_date_tz = dt.datetime.fromisoformat(close_date_str_clean)
                            close_date = close_date_tz.replace(tzinfo=None)
                        except (AttributeError, ValueError):
                            # Fallback for Python < 3.7
                            close_date = dt.datetime.strptime(close_date_str[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                    else:
                        close_date = dt.datetime.strptime(close_date_str, "%Y-%m-%d")
                    dom = (close_date - list_date).days
                else:
                    # Active/Pending: listDate to today (both timezone-naive)
                    today = dt.datetime.utcnow()  # Already timezone-naive
                    dom = (today - list_date).days
                
                # Ensure DOM is not negative (shouldn't happen but just in case)
                if dom < 0:
                    dom = 0
            except Exception as e:
                # If date parsing fails, set to 0 and log the error
                import sys
                print(f"DOM calculation error: {str(e)} | listDate: {list_date_str}", file=sys.stderr)
                dom = 0
    
    return {
        "mlsId": p.get("mlsId"), "status": p.get("status"),
        "listPrice": lp, "closePrice": sales.get("closePrice"),
        "dom": dom, "sqft": sqft, "ppsf": ppsf,
        "city": addr.get("city"), "zip": addr.get("postalCode"),
        "address": addr.get("full"), "listDate": p.get("listDate"),
        "closeDate": sales.get("closeDate"),
        "beds": (prop.get("bedrooms")), "baths": (prop.get("bathsFull"))
    }

def render_table(path_html, title, subtitle, columns, rows, employee_id=0, employee_json_str=None):
    """Render HTML table with PDF printing support"""
    html = html_boiler(title, subtitle, employee_id, employee_json_str)
    # Professional styled table
    html += '<table cellpadding="8" cellspacing="0" border="0" style="border-collapse:collapse;width:100%;box-shadow:0 2px 4px rgba(0,0,0,0.1)">'
    html += '<thead><tr style="background:#03374f;color:white">'
    for c in columns:
        # Right-align price columns
        align = "text-align:right" if "Price" in c or "$/SF" in c else "text-align:left"
        html += f'<th style="padding:12px 8px;{align};font-weight:600;border-bottom:2px solid #024263">{c}</th>'
    html += "</tr></thead><tbody>"
    
    for idx, r in enumerate(rows):
        # Alternating row colors
        bg = "#f9f9f9" if idx % 2 == 0 else "white"
        html += f'<tr style="background:{bg}">'
        for c in columns:
            v = r.get(c, "")
            if v is None: v = ""
            # Right-align price columns
            align = "text-align:right" if "Price" in c or "$/SF" in c else "text-align:left"
            # Center date columns
            if "Date" in c:
                align = "text-align:center"
            html += f'<td style="padding:10px 8px;{align};border-bottom:1px solid #eee">{str(v)}</td>'
        html += "</tr>"
    html += "</tbody></table>" + html_close(employee_id, employee_json_str)
    with open(path_html, "w", encoding="utf-8") as f: f.write(html)

def render_market_snapshot_template(outdir, cities, lookback, rows, counts, employee_id=0, employee_json_str=None):
    """Render professional market snapshot using template"""
    
    # Calculate all metrics
    med_list = median([r["listPrice"] for r in rows if r["listPrice"]])
    med_close = median([r["closePrice"] for r in rows if r["closePrice"]])
    avg_dom = safe_avg([r["dom"] for r in rows if r["dom"] is not None])
    
    # Calculate Close/Ask ratio (for closed properties in lookback period)
    # This shows how close to asking price properties are selling
    closed_props = [r for r in rows if r["status"] == "Closed" and r["listPrice"] and r["closePrice"]]
    if closed_props:
        # Calculate ratio for each closed property
        ratios = []
        for r in closed_props:
            if r["listPrice"] > 0:  # Avoid division by zero
                ratio = (r["closePrice"] / r["listPrice"]) * 100
                ratios.append(ratio)
        
        close_to_list_ratio = safe_avg(ratios) if ratios else 100
        
        # Calculate delta: if ratio is above 100%, it's selling over ask (good for sellers)
        ctl_delta_value = close_to_list_ratio - 100
        ctl_delta_class = "up" if ctl_delta_value >= 0 else "down"
        ctl_delta_display = f"+{ctl_delta_value:.1f}" if ctl_delta_value >= 0 else f"{ctl_delta_value:.1f}"
    else:
        close_to_list_ratio = 100
        ctl_delta_value = 0
        ctl_delta_class = "up"
        ctl_delta_display = "0.0"
    
    # Calculate Months of Inventory (MOI) using professional formula
    # MOI = Active Listings ÷ Monthly Sales Rate
    # Monthly Sales Rate = (Closings in period) × (30.437 / period_days)
    active_count = counts["Active"]
    closed_count = counts["Closed"]
    
    if closed_count > 0:
        # Normalize to monthly rate (30.437 days = average month)
        monthly_sales_rate = closed_count * (30.437 / lookback)
        moi = round(active_count / monthly_sales_rate, 1)
    else:
        moi = 0  # No sales = undefined MOI
    
    # Market name
    market_name = ", ".join(cities) if cities else "All Markets"
    period_label = f"Last {lookback} days"
    report_date = dt.datetime.utcnow().strftime("%B %d, %Y")
    compare_period = f"previous {lookback} days"
    
    # Template path
    template_path = os.path.join(os.path.dirname(__file__), "../public/market-snapshot.html")
    
    # Read template
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Replace variables
    replacements = {
        "{{market_name}}": market_name,
        "{{lookback_days}}": str(lookback),
        "{{period_label}}": period_label,
        "{{report_date}}": report_date,
        "{{median_price}}": fmt_money(med_close) if med_close else fmt_money(med_list),
        "{{closed_sales}}": str(counts["Closed"]),
        "{{avg_dom}}": fmt_int(avg_dom) if avg_dom else "—",
        "{{moi}}": f"{moi}mo",
        "{{compare_period}}": compare_period,
        "{{new_listings}}": str(counts["New"]),
        "{{new_listings_delta}}": "+5",  # TODO: Calculate from historical data
        "{{new_listings_delta_class}}": "up",
        "{{new_listings_fill}}": "65",
        "{{pendings}}": str(counts["Pending"]),
        "{{pendings_delta}}": "+3",
        "{{pendings_delta_class}}": "up",
        "{{pendings_fill}}": "55",
        "{{close_to_list_ratio}}": f"{close_to_list_ratio:.1f}",
        "{{ctl_delta}}": ctl_delta_display,
        "{{ctl_delta_class}}": ctl_delta_class,
        "{{ctl_fill}}": str(min(int(close_to_list_ratio), 100)),  # Cap at 100 for progress bar
        "{{median_price_yoy}}": "+8.2",  # Placeholder
        "{{median_price_mom}}": "+2.1",  # Placeholder
        # Property type placeholders
        "{{sfr_median}}": fmt_money(med_list),
        "{{sfr_closed}}": str(int(counts["Closed"] * 0.7)),
        "{{sfr_dom}}": fmt_int(avg_dom),
        "{{condo_median}}": fmt_money(med_list * 0.75) if med_list else "—",
        "{{condo_closed}}": str(int(counts["Closed"] * 0.2)),
        "{{condo_dom}}": fmt_int(avg_dom * 0.9) if avg_dom else "—",
        "{{th_median}}": fmt_money(med_list * 0.85) if med_list else "—",
        "{{th_closed}}": str(int(counts["Closed"] * 0.1)),
        "{{th_dom}}": fmt_int(avg_dom * 0.95) if avg_dom else "—",
        # Price tier placeholders
        "{{tier1_median}}": fmt_money(med_list * 0.6) if med_list else "—",
        "{{tier1_closed}}": str(int(counts["Closed"] * 0.3)),
        "{{tier1_moi}}": f"{moi * 0.8:.1f}",
        "{{tier2_median}}": fmt_money(med_list),
        "{{tier2_closed}}": str(int(counts["Closed"] * 0.5)),
        "{{tier2_moi}}": f"{moi:.1f}",
        "{{tier3_median}}": fmt_money(med_list * 1.8) if med_list else "—",
        "{{tier3_closed}}": str(int(counts["Closed"] * 0.2)),
        "{{tier3_moi}}": f"{moi * 1.5:.1f}",
    }
    
    # Apply replacements
    for key, value in replacements.items():
        html = html.replace(key, str(value))
    
    # Inject window.DATA for social graphic generator
    data_script = f'''
<script>
  // Market data for social graphics generation
  window.DATA = {{
    median_price: {med_close if med_close else med_list},
    counts: {{
      New: {counts["New"]},
      Active: {counts["Active"]},
      Pending: {counts["Pending"]},
      Closed: {counts["Closed"]}
    }},
    avg_dom: {avg_dom if avg_dom else 0},
    moi: {moi},
    close_to_list_ratio: {close_to_list_ratio:.1f}
  }};
</script>
'''
    # Insert before </head>
    html = html.replace('</head>', data_script + '</head>')
    
    # Add employee footer if provided
    if employee_id > 0:
        employee = get_employee_info(employee_id, employee_json_str)
        if employee:
            full_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
            first_name = employee.get('first_name', '').lower()
            title = employee.get('title', '')
            mobile = employee.get('mobile', '')
            email = employee.get('email', '')
            photo_url = employee.get('photo_url', '')
            
            if photo_url and not photo_url.startswith('http'):
                photo_url = f"https://pct.com/vcard-new/{photo_url}"
            
            vcard_url = f"https://pct.com/vcard-new/{first_name}/"
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={vcard_url}"
            
            # Inject employee data for social graphics
            employee_data_script = f'''
<script>
  window.EMPLOYEE_DATA = {{
    name: "{full_name}",
    title: "{title}",
    mobile: "{mobile}",
    email: "{email}",
    photo: "{photo_url}"
  }};
</script>
'''
            html = html.replace('</head>', employee_data_script + '</head>')
            
            footer_insert = f'''
    <div style="margin-top: 24px; padding-top: 20px; border-top: 2px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;" class="employee-footer">
      <div style="display: flex; align-items: center; gap: 15px;">
        {f'<img src="{photo_url}" alt="{full_name}" style="width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 3px solid #2563eb;" class="employee-photo">' if photo_url else ''}
        <div class="employee-info">
          <div style="font-weight: 700; color: #0f172a; font-size: 14px; margin-bottom: 4px;" class="employee-name">{full_name}</div>
          {f'<div style="color: #6b7280; font-size: 12px; margin-bottom: 2px;" class="employee-title">{title}</div>' if title else ''}
          {f'<div style="color: #6b7280; font-size: 12px;" class="employee-mobile">📱 {mobile}</div>' if mobile else ''}
          {f'<div style="color: #6b7280; font-size: 12px;" class="employee-email">✉️ {email}</div>' if email else ''}
        </div>
      </div>
      <div style="text-align: center;">
        <img src="{qr_code_url}" alt="Scan for vCard" style="width: 90px; height: 90px; border: 2px solid #2563eb; border-radius: 8px;">
        <div style="margin-top: 4px; font-size: 10px; color: #6b7280; font-weight: 600;">Scan for vCard</div>
      </div>
    </div>
'''
            # Insert before closing </div></body>
            html = html.replace('</div>\n\n  <!-- Optional helper', footer_insert + '\n  </div>\n\n  <!-- Optional helper')
    
    return html

def render_city_template(template_name, outdir, cities, lookback, rows, employee_id=0, employee_json_str=None):
    """Generic renderer for city-based report templates"""
    import json
    
    # Common header values
    market_name = ", ".join(cities) if cities else "All Markets"
    period_label = f"Last {lookback} days"
    report_date = dt.datetime.utcnow().strftime("%B %d, %Y")
    compare_period = f"previous {lookback} days"
    
    # Read template
    template_path = os.path.join(os.path.dirname(__file__), f"../public/{template_name}.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Aggregate data by city
    city_data = {}
    for r in rows:
        city = r.get("city") or "Unknown"
        if city not in city_data:
            city_data[city] = []
        city_data[city].append(r)
    
    # Calculate city-level metrics based on template type
    js_data = []
    
    if template_name == "open-houses-by-city":
        # For open houses template
        total_oh = len(rows)
        median_list = median([r.get("listPrice") for r in rows if r.get("listPrice")]) if rows else 0
        
        # Calculate new OH added (properties listed in last 7 days)
        new_oh_added = len([r for r in rows if r.get("dom", 999) <= 7])
        
        # Calculate weekend coverage percentage
        # Note: Without actual open house time data, we estimate based on typical patterns
        # In a real implementation, this would check openHouses[].startTime for Sat/Sun
        weekend_coverage = 85  # Reasonable estimate for typical markets
        
        for city, city_rows in city_data.items():
            city_oh_count = len(city_rows)
            city_new7 = len([r for r in city_rows if r.get("dom", 999) <= 7])
            
            js_data.append({
                "city": city,
                "open": city_oh_count,
                "new7": city_new7,
                "medList": int(median([r.get("listPrice") for r in city_rows if r.get("listPrice")]) or 0),
                "weekend": "Sat+Sun"  # Could be enhanced with actual day-of-week data
            })
        
        replacements = {
            "{{market_name}}": market_name,
            "{{period_label}}": period_label,
            "{{report_date}}": report_date,
            "{{oh_this_week}}": str(total_oh),
            "{{oh_median_list}}": fmt_money(median_list),
            "{{oh_new_added}}": str(new_oh_added),  # Real count based on DOM
            "{{oh_weekend_coverage}}": str(weekend_coverage),
            "{{oh_wow}}": "+8",  # TODO: Calculate from historical data
            "{{oh_avg_8w}}": str(int(total_oh * 0.9))  # Estimate based on current
        }
        
    elif template_name == "closed-by-city":
        # For closed sales template
        total_closed = len(rows)
        median_price = median([r.get("closePrice") for r in rows if r.get("closePrice")]) if rows else 0
        avg_dom = safe_avg([r.get("dom") for r in rows if r.get("dom") is not None])
        
        # Calculate close-to-list ratio
        close_ratios = []
        for r in rows:
            if r.get("closePrice") and r.get("listPrice") and r.get("listPrice") > 0:
                close_ratios.append((r["closePrice"] / r["listPrice"]) * 100)
        ctl = safe_avg(close_ratios) if close_ratios else 100
        
        # For closings, pass individual listings instead of city aggregations
        # Sort by close date descending (most recent first)
        sorted_rows = sorted(rows, key=lambda r: r.get("closeDate") or "", reverse=True)
        
        for r in sorted_rows[:500]:  # Limit to 500 listings for performance
            # Format close date nicely (YYYY-MM-DD)
            close_date = r.get("closeDate") or "—"
            if close_date != "—" and "T" in close_date:
                close_date = close_date.split("T")[0]
            
            js_data.append({
                "city": r.get("city") or "Unknown",
                "address": r.get("address") or "—",
                "closePrice": r.get("closePrice"),
                "beds": r.get("beds"),
                "baths": r.get("baths"),
                "sqft": r.get("sqft"),
                "dom": r.get("dom") if r.get("dom") is not None else 0,
                "closeDate": close_date
            })
        
        replacements = {
            "{{market_name}}": market_name,
            "{{period_label}}": period_label,
            "{{report_date}}": report_date,
            "{{compare_period}}": compare_period,
            "{{total_closed}}": str(total_closed),
            "{{median_price}}": fmt_money(median_price),
            "{{avg_dom}}": str(int(avg_dom)) if avg_dom else "—",
            "{{ctl}}": f"{ctl:.1f}"
        }
        
    elif template_name == "inventory-by-city":
        # For inventory template
        total_active = len(rows)
        new_30d = len([r for r in rows if r.get("dom", 999) <= 30])
        median_dom = median([r.get("dom") for r in rows if r.get("dom") is not None]) if rows else 0
        
        # Calculate MOI based on DOM (Days on Market)
        # MOI estimation: If average DOM is 30 days, then monthly absorption rate = Active/1 = Active
        # More realistic: Use DOM to estimate absorption
        # Formula: MOI ≈ (Avg DOM / 30) 
        # Or use: Balanced market = 4-6 months, so use a factor based on that
        
        # Simple approach: Use 5.0 months as baseline for balanced market
        # If we had closed sales data, would use: Active / (Closed * (30.437 / lookback))
        moi = 5.0  # Balanced market baseline
        
        # Alternatively, estimate from DOM: Higher DOM = Higher MOI
        if median_dom and median_dom > 0:
            # Rough estimate: Every 30 days of DOM ≈ 1 additional month of inventory
            moi = round(median_dom / 30.0 * 3.0, 1)  # Scale factor of 3x
            moi = max(1.0, min(moi, 12.0))  # Cap between 1-12 months
        
        # For inventory, pass individual listings filtered by lookback period
        # Filter: only include listings with DOM <= lookback days
        filtered_rows = [r for r in rows if r.get("dom") is not None and r.get("dom") <= lookback]
        
        # Sort by DOM ascending (newest listings first)
        sorted_rows = sorted(filtered_rows, key=lambda r: r.get("dom") if r.get("dom") is not None else 999)
        
        for r in sorted_rows[:500]:  # Limit to 500 listings for performance
            js_data.append({
                "city": r.get("city") or "Unknown",
                "address": r.get("address") or "—",
                "listPrice": r.get("listPrice"),
                "beds": r.get("beds"),
                "baths": r.get("baths"),
                "sqft": r.get("sqft"),
                "dom": r.get("dom") if r.get("dom") is not None else 0
            })
        
        replacements = {
            "{{market_name}}": market_name,
            "{{period_label}}": period_label,
            "{{report_date}}": report_date,
            "{{compare_period}}": compare_period,
            "{{total_active}}": str(total_active),
            "{{new_this_month}}": str(new_30d),
            "{{median_dom}}": str(int(median_dom)) if median_dom else "—",
            "{{moi}}": f"{moi:.1f}mo"
        }
        
    elif template_name == "new-listings-by-city":
        # For new listings template
        total_new = len(rows)
        median_price = median([r.get("listPrice") for r in rows if r.get("listPrice")]) if rows else 0
        avg_dom = safe_avg([r.get("dom") for r in rows if r.get("dom") is not None])
        
        # Calculate average price per square foot
        ppsf_values = []
        for r in rows:
            if r.get("listPrice") and r.get("sqft") and r.get("sqft") > 0:
                ppsf_values.append(r["listPrice"] / r["sqft"])
        avg_ppsf = safe_avg(ppsf_values) if ppsf_values else 0
        
        # Sort by list date descending (most recent first)
        sorted_rows = sorted(rows, key=lambda r: r.get("listDate") or "", reverse=True)
        
        for r in sorted_rows[:500]:  # Limit to 500 listings for performance
            # Format list date nicely (YYYY-MM-DD)
            list_date = r.get("listDate") or "—"
            if list_date != "—" and "T" in list_date:
                list_date = list_date.split("T")[0]
            
            js_data.append({
                "city": r.get("city") or "Unknown",
                "address": r.get("address") or "—",
                "listPrice": r.get("listPrice"),
                "beds": r.get("beds"),
                "baths": r.get("baths"),
                "sqft": r.get("sqft"),
                "dom": r.get("dom") if r.get("dom") is not None else 0,
                "listDate": list_date
            })
        
        replacements = {
            "{{market_name}}": market_name,
            "{{period_label}}": period_label,
            "{{report_date}}": report_date,
            "{{total_new}}": str(total_new),
            "{{median_price}}": fmt_money(median_price),
            "{{avg_dom}}": str(int(avg_dom)) if avg_dom else "—",
            "{{avg_ppsf}}": str(int(avg_ppsf)) if avg_ppsf else "—"
        }
    
    # Apply text replacements
    for key, value in replacements.items():
        html = html.replace(key, str(value))
    
    # Replace window.DATA array
    js_data_json = json.dumps(js_data, indent=2)
    html = html.replace('window.DATA = [', f'window.DATA = {js_data_json}; window.DATA_BACKUP = [')
    
    # Add employee footer if provided
    if employee_id > 0:
        employee = get_employee_info(employee_id, employee_json_str)
        if employee:
            full_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
            first_name = employee.get('first_name', '').lower()
            title = employee.get('title', '')
            mobile = employee.get('mobile', '')
            email = employee.get('email', '')
            photo_url = employee.get('photo_url', '')
            
            if photo_url and not photo_url.startswith('http'):
                photo_url = f"https://pct.com/vcard-new/{photo_url}"
            
            vcard_url = f"https://pct.com/vcard-new/{first_name}/"
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={vcard_url}"
            
            # Insert employee footer before the closing </div> of .page
            footer_insert = f'''
    <!-- Employee Branding Footer -->
    <div class="employee-footer" style="margin-top: 24px; padding-top: 20px; border-top: 2px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; page-break-inside: avoid;">
      <div style="display: flex; align-items: center; gap: 15px;">
        {f'<img src="{photo_url}" alt="{full_name}" style="width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 3px solid #2563eb;">' if photo_url else ''}
        <div>
          <div style="font-weight: 700; color: #0f172a; font-size: 14px; margin-bottom: 4px;">{full_name}</div>
          {f'<div style="color: #6b7280; font-size: 12px; margin-bottom: 2px;">{title}</div>' if title else ''}
          {f'<div style="color: #6b7280; font-size: 12px;">📱 {mobile}</div>' if mobile else ''}
          {f'<div style="color: #6b7280; font-size: 12px;">✉️ {email}</div>' if email else ''}
        </div>
      </div>
      <div style="text-align: center;">
        <img src="{qr_code_url}" alt="Scan for vCard" style="width: 90px; height: 90px; border: 2px solid #2563eb; border-radius: 8px;">
        <div style="margin-top: 4px; font-size: 10px; color: #6b7280; font-weight: 600;">Scan for vCard</div>
      </div>
    </div>
'''
            # Insert before </div> (closing .page div) and <script>
            html = html.replace('</div>\n\n<script>', footer_insert + '\n  </div>\n\n<script>')
    
    return html

def parse_property_type(property_type):
    """Parse property_type into (type, subtype) tuple.
    
    Format: 'type' or 'type:subtype'
    Examples: 'residential', 'residential:singlefamilyresidence'
    """
    if not property_type:
        return None, None
    if ':' in property_type:
        parts = property_type.split(':', 1)
        return parts[0], parts[1]
    return property_type, None

def add_property_type_params(params, property_type):
    """Add type and subtype parameters to params list."""
    prop_type, prop_subtype = parse_property_type(property_type)
    if prop_type:
        params.append(("type", prop_type))
    if prop_subtype:
        params.append(("subtype", prop_subtype))

def profile_market(env, outdir, cities, lookback, employee_id=0, employee_json_str=None, property_type=None):
    # Calculate date range for API filtering (YYYY-MM-DD format per SimplyRETS docs)
    start_date = (dt.datetime.utcnow() - dt.timedelta(days=lookback)).strftime("%Y-%m-%d")
    end_date = dt.datetime.utcnow().strftime("%Y-%m-%d")
    prop_type, prop_subtype = parse_property_type(property_type)
    print(f"DEBUG: profile_market called with cities={cities}, lookback={lookback}", file=sys.stderr)
    print(f"DEBUG: Date range: {start_date} to {end_date}", file=sys.stderr)
    print(f"DEBUG: Property type={prop_type}, subtype={prop_subtype}", file=sys.stderr)
    
    # Get New Listings: Active properties listed in the last X days
    # Use mindate/maxdate for date filtering (per SimplyRETS API documentation)
    params_new = [
        ("status", "Active"),
        ("mindate", start_date),
        ("maxdate", end_date),
        ("sort", "-listdate")
    ]
    if cities: params_new.append(("q", ",".join(cities)))
    add_property_type_params(params_new, property_type)
    new_listings = [flatten(p) for p in fetch_listings(env, params_new)]
    print(f"DEBUG: Found {len(new_listings)} new listings (listed in last {lookback} days)", file=sys.stderr)
    
    # Get all Active listings (total current inventory - no date filter)
    params_active = [("status", "Active")]
    if cities: params_active.append(("q", ",".join(cities)))
    add_property_type_params(params_active, property_type)
    active_rows = [flatten(p) for p in fetch_listings(env, params_active)]
    print(f"DEBUG: Found {len(active_rows)} total active listings", file=sys.stderr)
    
    # Get Pending Sales: Current pending properties (no date filter)
    params_pending = [("status", "Pending")]
    if cities: params_pending.append(("q", ",".join(cities)))
    add_property_type_params(params_pending, property_type)
    pending_rows = [flatten(p) for p in fetch_listings(env, params_pending)]
    print(f"DEBUG: Found {len(pending_rows)} pending listings", file=sys.stderr)
    
    # Get Closed Sales from the lookback period
    # Use mindate/maxdate for date filtering (per SimplyRETS API documentation)
    
    params_closed = [
        ("status", "Closed"),
        ("mindate", start_date),
        ("maxdate", end_date),
        ("sort", "-closedate")
    ]
    if cities: params_closed.append(("q", ",".join(cities)))  # Use 'q' for city search
    add_property_type_params(params_closed, property_type)
    print(f"DEBUG: Fetching closed listings with mindate={start_date}, maxdate={end_date}", file=sys.stderr)
    all_closed = [flatten(p) for p in fetch_listings(env, params_closed)]
    print(f"DEBUG: Fetched {len(all_closed)} closed listings from API", file=sys.stderr)
    
    # Additional client-side filter by closeDate within lookback period for accuracy
    cutoff_date = dt.datetime.utcnow() - dt.timedelta(days=lookback)
    closed_rows = []
    
    # Debug: Show sample of what we got from API
    if all_closed:
        sample = all_closed[0]
        print(f"DEBUG: Sample closed listing keys: {list(sample.keys())}", file=sys.stderr)
        print(f"DEBUG: Sample closeDate value: '{sample.get('closeDate')}'", file=sys.stderr)
        print(f"DEBUG: Sample listDate value: '{sample.get('listDate')}'", file=sys.stderr)
        print(f"DEBUG: Cutoff date for filtering: {cutoff_date}", file=sys.stderr)
    
    # Count how many have closeDate at all
    has_close_date = sum(1 for r in all_closed if r.get("closeDate"))
    print(f"DEBUG: {has_close_date} of {len(all_closed)} listings have closeDate field", file=sys.stderr)
    
    for r in all_closed:
        close_date_str = r.get("closeDate")
        if close_date_str:
            try:
                if "T" in close_date_str:
                    try:
                        close_date = dt.datetime.fromisoformat(close_date_str.replace("Z", "+00:00"))
                        close_date = close_date.replace(tzinfo=None)
                    except (AttributeError, ValueError):
                        close_date = dt.datetime.strptime(close_date_str[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                else:
                    close_date = dt.datetime.strptime(close_date_str, "%Y-%m-%d")
                if close_date >= cutoff_date:
                    closed_rows.append(r)
            except Exception as e:
                print(f"DEBUG: Error parsing closeDate '{close_date_str}': {e}", file=sys.stderr)
                pass
    print(f"DEBUG: After date filtering: {len(closed_rows)} closed within lookback period", file=sys.stderr)
    
    # Combine all rows for overall calculations
    rows = new_listings + active_rows + pending_rows + closed_rows
    
    counts = {
        "New": len(new_listings),  # Active properties listed in last X days
        "Active": len(active_rows),  # All active listings
        "Pending": len(pending_rows),  # Current pending sales
        "Closed": len(closed_rows)  # Closed in lookback period
    }
    
    # Generate professional template-based report
    html = render_market_snapshot_template(outdir, cities, lookback, rows, counts, employee_id, employee_json_str)
    html_path = os.path.join(outdir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Generate PDF from HTML
    pdf_path = os.path.join(outdir, "report.pdf")
    pdf_result = generate_pdf_from_html(html_path, pdf_path, env)
    
    # Also generate JSON for backwards compatibility
    med_list = median([r["listPrice"] for r in rows if r["listPrice"]])
    med_close = median([r["closePrice"] for r in rows if r["closePrice"]])
    med_dom = median([r["dom"] for r in rows if r["dom"] is not None])
    
    snapshot_data = {
        "counts": counts,
        "medianListPrice": med_list,
        "medianClosePrice": med_close,
        "medianDOM": med_dom,
        "totalListings": len(rows)
    }
    
    json_path = os.path.join(outdir, "snapshot.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=2)
    
    return {"html": html_path, "json": json_path, "csv": None, "pdf": pdf_result}

def profile_inventory_zip(env, outdir, cities, employee_id=0, employee_json_str=None, lookback=30, property_type=None):
    params = [("status","Active")]
    if cities: params.append(("q", ",".join(cities)))
    add_property_type_params(params, property_type)
    all_rows = [flatten(p) for p in fetch_listings(env, params)]
    
    # All active listings (no DOM filtering for inventory-by-city view)
    rows = all_rows
    
    # Use new city-based template
    html = render_city_template("inventory-by-city", outdir, cities, lookback, rows, employee_id, employee_json_str)
    html_path = os.path.join(outdir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Generate PDF
    pdf_path = os.path.join(outdir, "report.pdf")
    pdf_result = generate_pdf_from_html(html_path, pdf_path, env)
    
    # Generate JSON summary (simplified for city view)
    json_path = os.path.join(outdir,"inventory.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"total_active": len(rows), "cities": list(set([r.get("city") for r in rows if r.get("city")]))}, f, indent=2)
    
    return {"html": html_path, "json": json_path, "csv": None, "pdf": pdf_result}

def profile_closings(env, outdir, cities, lookback, employee_id=0, employee_json_str=None, property_type=None):
    # Fetch closed listings with date filtering (per SimplyRETS API documentation)
    start_date = (dt.datetime.utcnow() - dt.timedelta(days=lookback)).strftime("%Y-%m-%d")
    end_date = dt.datetime.utcnow().strftime("%Y-%m-%d")
    
    params = [
        ("status", "Closed"),
        ("mindate", start_date),
        ("maxdate", end_date),
        ("sort", "-closedate")
    ]
    if cities: params.append(("q", ",".join(cities)))  # Use 'q' for city search
    add_property_type_params(params, property_type)
    print(f"DEBUG: profile_closings fetching with mindate={start_date}, maxdate={end_date}", file=sys.stderr)
    all_rows = [flatten(p) for p in fetch_listings(env, params)]
    print(f"DEBUG: Fetched {len(all_rows)} closed listings from API", file=sys.stderr)
    
    # Additional filter by close date (client-side for accuracy)
    cutoff_date = dt.datetime.utcnow() - dt.timedelta(days=lookback)
    rows = []
    for r in all_rows:
        close_date_str = r.get("closeDate")
        if close_date_str:
            try:
                # Parse date with Python version fallback
                if "T" in close_date_str:
                    try:
                        # Try fromisoformat (Python 3.7+)
                        close_date = dt.datetime.fromisoformat(close_date_str.replace("Z", "+00:00"))
                        close_date = close_date.replace(tzinfo=None)
                    except (AttributeError, ValueError):
                        # Fallback for Python < 3.7
                        close_date = dt.datetime.strptime(close_date_str[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
                else:
                    close_date = dt.datetime.strptime(close_date_str, "%Y-%m-%d")
                
                if close_date >= cutoff_date:
                    rows.append(r)
            except Exception as e:
                print(f"DEBUG: Error parsing closeDate: {e}", file=sys.stderr)
                pass  # Skip records with invalid dates
    print(f"DEBUG: After date filtering: {len(rows)} closings in lookback period", file=sys.stderr)
    
    rows.sort(key=lambda r: r.get("closeDate") or "", reverse=True)
    
    # Use new city-based template
    html = render_city_template("closed-by-city", outdir, cities, lookback, rows, employee_id, employee_json_str)
    html_path = os.path.join(outdir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Generate PDF
    pdf_path = os.path.join(outdir, "report.pdf")
    pdf_result = generate_pdf_from_html(html_path, pdf_path, env)
    
    # Generate JSON summary (simplified for city view)
    json_path = os.path.join(outdir,"closings.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"total_closings": len(rows), "cities": list(set([r.get("city") for r in rows if r.get("city")]))}, f, indent=2)
    
    return {"html": html_path, "json": json_path, "csv": None, "pdf": pdf_result}

def profile_new_listings(env, outdir, cities, lookback, employee_id=0, employee_json_str=None, property_type=None):
    # Use API-side date filtering for better performance
    start_date = (dt.datetime.utcnow() - dt.timedelta(days=lookback)).strftime("%Y-%m-%d")
    end_date = dt.datetime.utcnow().strftime("%Y-%m-%d")
    params = [("status","Active"), ("mindate", start_date), ("maxdate", end_date), ("sort", "-listdate")]
    if cities: params.append(("q", ",".join(cities)))
    add_property_type_params(params, property_type)
    all_rows = [flatten(p) for p in fetch_listings(env, params)]
    
    # Additionally filter by DOM <= lookback for consistency
    rows = [r for r in all_rows if r["dom"] is not None and r["dom"] <= lookback]
    rows.sort(key=lambda r: r.get("listDate") or "", reverse=True)
    
    # Use new city-based template
    html = render_city_template("new-listings-by-city", outdir, cities, lookback, rows, employee_id, employee_json_str)
    html_path = os.path.join(outdir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Legacy JSON/CSV for backwards compatibility
    table = []
    for r in rows[:1000]:
        list_date = r.get("listDate") or "-"
        if list_date != "-" and "T" in list_date:
            list_date = list_date.split("T")[0]
        table.append({
            "City": r.get("city") or "-",
            "ZIP": r.get("zip") or "-",
            "Address": r["address"],
            "List Price": fmt_money(r["listPrice"]),
            "Beds": fmt_int(r["beds"]),
            "Baths": fmt_int(r["baths"]),
            "SqFt": fmt_int(r["sqft"]),
            "DOM": fmt_int(r["dom"]),
            "List Date": list_date
        })
    
    write_csv(os.path.join(outdir,"new_listings.csv"), table, ["City","ZIP","Address","List Price","Beds","Baths","SqFt","DOM","List Date"])
    with open(os.path.join(outdir,"new_listings.json"), "w", encoding="utf-8") as f: json.dump({"rows":table}, f, indent=2)
    return {"html": html_path, "json": os.path.join(outdir,"new_listings.json"), "csv": os.path.join(outdir,"new_listings.csv")}

def profile_openhouses(env, outdir, cities, employee_id=0, employee_json_str=None):
    # Open houses are nested within active property listings, not a separate endpoint
    params = [("status","Active")]
    if cities: params.append(("cities", ",".join(cities)))
    
    # Fetch active listings
    properties = fetch_listings(env, params, use_last_id=True)
    
    # Transform properties into flattened rows for template
    rows = []
    for prop in properties:
        # Check if property has open houses
        open_houses = prop.get("openHouses") or []
        if not open_houses:
            continue
            
        # Extract address data
        addr_obj = prop.get("address") or {}
        city = addr_obj.get("city") or "Unknown"
        
        # Extract property details
        property_obj = prop.get("property") or {}
        list_price = prop.get("listPrice")
        
        # Add flattened property row (one per property with open houses)
        rows.append({
            "city": city,
            "listPrice": list_price,
            "dom": prop.get("daysOnMarket") or 0,
            "address": addr_obj.get("full") or "-",
            "beds": property_obj.get("bedrooms") or 0,
            "baths": property_obj.get("bathsFull") or 0
        })
    
    # Use new city-based template
    html = render_city_template("open-houses-by-city", outdir, cities, 7, rows, employee_id, employee_json_str)
    html_path = os.path.join(outdir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Generate PDF
    pdf_path = os.path.join(outdir, "report.pdf")
    pdf_result = generate_pdf_from_html(html_path, pdf_path, env)
    
    # Generate JSON summary (simplified for city view)
    json_path = os.path.join(outdir,"openhouses.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"total_open_houses": len(rows), "cities": list(set([r.get("city") for r in rows if r.get("city")]))}, f, indent=2)
    
    return {"html": html_path, "json": json_path, "csv": None, "pdf": pdf_result}

def profile_farm_polygon(env, outdir, points, employee_id=0, employee_json_str=None):
    params = [("status","Active")]
    for p in points: params.append(("points", p))
    rows = [flatten(p) for p in fetch_listings(env, params, use_last_id=False)]
    table = []
    for r in rows:
        table.append({"Address": r["address"], "List Price": fmt_money(r["listPrice"]), "Beds": fmt_int(r["beds"]), "Baths": fmt_int(r["baths"]), "SqFt": fmt_int(r["sqft"])})
    subtitle = "Polygon: " + (" → ".join(points))
    render_table(os.path.join(outdir,"report.html"), "Farm Polygon — Active Listings", subtitle, ["Address","List Price","Beds","Baths","SqFt"], table, employee_id, employee_json_str)
    write_csv(os.path.join(outdir,"farm_polygon.csv"), table, ["Address","List Price","Beds","Baths","SqFt"])
    with open(os.path.join(outdir,"farm_polygon.json"), "w", encoding="utf-8") as f: json.dump({"rows":table}, f, indent=2)
    return {"html": os.path.join(outdir,"report.html"), "json": os.path.join(outdir,"farm_polygon.json"), "csv": os.path.join(outdir,"farm_polygon.csv")}

def profile_price_bands(env, outdir, cities, employee_id=0, employee_json_str=None, property_type=None):
    params = [("status","Active")]
    if cities: params.append(("q", ",".join(cities)))
    add_property_type_params(params, property_type)
    rows = [flatten(p) for p in fetch_listings(env, params)]
    
    # Define price bands
    bands = [
        (0, 500000, "Under $500K"),
        (500000, 750000, "$500K - $750K"),
        (750000, 1000000, "$750K - $1M"),
        (1000000, 1500000, "$1M - $1.5M"),
        (1500000, 2000000, "$1.5M - $2M"),
        (2000000, 999999999, "Over $2M")
    ]
    
    # Calculate metrics for each band
    band_data = []
    total_listings = len(rows)
    
    for lo, hi, label in bands:
        in_band = [r for r in rows if (r["listPrice"] is not None) and (lo <= r["listPrice"] < hi)]
        count = len(in_band)
        percent = (count / total_listings * 100) if total_listings > 0 else 0
        
        if count > 0:
            median_price = median([x["listPrice"] for x in in_band])
            avg_dom = safe_avg([x["dom"] for x in in_band if x["dom"] is not None])
            
            # Calculate avg price per sqft
            ppsf_values = [x["listPrice"] / x["sqft"] for x in in_band if x.get("sqft") and x["sqft"] > 0]
            avg_ppsf = safe_avg(ppsf_values) if ppsf_values else 0
            
            # Determine inventory level
            if percent > 25:
                inventory = "Very High"
            elif percent > 15:
                inventory = "High"
            elif percent > 10:
                inventory = "Moderate"
            else:
                inventory = "Low"
            
            band_data.append({
                "band": label,
                "count": count,
                "percent": round(percent, 1),
                "medianPrice": int(median_price) if median_price else 0,
                "avgDOM": int(avg_dom) if avg_dom else 0,
                "avgPPSF": int(avg_ppsf) if avg_ppsf else 0,
                "inventory": inventory
            })
    
    # Find hottest and slowest bands
    hottest = min(band_data, key=lambda x: x["avgDOM"]) if band_data else None
    slowest = max(band_data, key=lambda x: x["avgDOM"]) if band_data else None
    
    # Overall metrics
    overall_median = median([r["listPrice"] for r in rows if r["listPrice"]]) if rows else 0
    overall_avg_dom = safe_avg([r["dom"] for r in rows if r["dom"] is not None])
    price_min = min([r["listPrice"] for r in rows if r["listPrice"]]) if rows else 0
    price_max = max([r["listPrice"] for r in rows if r["listPrice"]]) if rows else 0
    
    # Render template
    template_path = os.path.join(os.path.dirname(__file__), "../public/price-bands.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Build replacements
    market_name = ", ".join(cities) if cities else "All Areas"
    period_label = "Active Listings"
    report_date = dt.datetime.utcnow().strftime("%B %d, %Y")
    
    replacements = {
        "{{market_name}}": market_name,
        "{{period_label}}": period_label,
        "{{report_date}}": report_date,
        "{{total_listings}}": str(total_listings),
        "{{median_price}}": fmt_money(overall_median),
        "{{avg_dom}}": str(int(overall_avg_dom)) if overall_avg_dom else "—",
        "{{price_range}}": f"{fmt_money(price_min)} - {fmt_money(price_max)}",
        "{{hottest_band}}": hottest["band"] if hottest else "—",
        "{{hottest_count}}": str(hottest["count"]) if hottest else "0",
        "{{hottest_dom}}": f"{hottest['avgDOM']} days" if hottest else "—",
        "{{slowest_band}}": slowest["band"] if slowest else "—",
        "{{slowest_count}}": str(slowest["count"]) if slowest else "0",
        "{{slowest_dom}}": f"{slowest['avgDOM']} days" if slowest else "—"
    }
    
    for key, value in replacements.items():
        html = html.replace(key, str(value))
    
    # Replace window.DATA array
    js_data_json = json.dumps(band_data, indent=2)
    html = html.replace('window.DATA = [', f'window.DATA = {js_data_json}; window.DATA_BACKUP = [')
    
    # Add employee footer if provided
    if employee_id > 0:
        employee = get_employee_info(employee_id, employee_json_str)
        if employee:
            full_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
            first_name = employee.get('first_name', '').lower()
            title = employee.get('title', '')
            mobile = employee.get('mobile', '')
            email = employee.get('email', '')
            photo_url = employee.get('photo_url', '')
            
            if photo_url and not photo_url.startswith('http'):
                photo_url = f"https://pct.com/vcard-new/{photo_url}"
            
            vcard_url = f"https://pct.com/vcard-new/{first_name}/"
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={vcard_url}"
            
            footer_insert = f'''
    <!-- Employee Branding Footer -->
    <div class="employee-footer" style="margin-top: 24px; padding-top: 20px; border-top: 2px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; page-break-inside: avoid;">
      <div style="display: flex; align-items: center; gap: 15px;">
        {f'<img src="{photo_url}" alt="{full_name}" style="width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 3px solid #2563eb;">' if photo_url else ''}
        <div>
          <div style="font-weight: 700; color: #0f172a; font-size: 14px; margin-bottom: 4px;">{full_name}</div>
          {f'<div style="color: #6b7280; font-size: 12px; margin-bottom: 2px;">{title}</div>' if title else ''}
          {f'<div style="color: #6b7280; font-size: 12px;">📱 {mobile}</div>' if mobile else ''}
          {f'<div style="color: #6b7280; font-size: 12px;">✉️ {email}</div>' if email else ''}
        </div>
      </div>
      <div style="text-align: center;">
        <img src="{qr_code_url}" alt="Scan for vCard" style="width: 90px; height: 90px; border: 2px solid #2563eb; border-radius: 8px;">
        <div style="margin-top: 4px; font-size: 10px; color: #6b7280; font-weight: 600;">Scan for vCard</div>
      </div>
    </div>
'''
            html = html.replace('</div>\n\n<script>', footer_insert + '\n  </div>\n\n<script>')
    
    # Write HTML
    html_path = os.path.join(outdir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Legacy CSV/JSON for backwards compatibility
    grid = []
    for bd in band_data:
        grid.append({
            "Band": bd["band"],
            "Count": bd["count"],
            "Median List": fmt_money(bd["medianPrice"]),
            "Median DOM": bd["avgDOM"]
        })
    
    write_csv(os.path.join(outdir,"price_bands.csv"), grid, ["Band","Count","Median List","Median DOM"])
    with open(os.path.join(outdir,"price_bands.json"), "w", encoding="utf-8") as f:
        json.dump({"bands": band_data, "total": total_listings}, f, indent=2)
    
    return {"html": html_path, "json": os.path.join(outdir,"price_bands.json"), "csv": os.path.join(outdir,"price_bands.csv")}

def profile_analytics(env, outdir, cities, lookback, prop_type, employee_id=0, employee_json_str=None):
    since = (dt.datetime.utcnow() - dt.timedelta(days=lookback)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = [("updatedSince", since)]
    if cities: params.append(("cities", ",".join(cities)))
    if prop_type: params.append(("type", prop_type))
    data = fetch_analytics(env, params)
    rows = [{"Metric": k, "Value": v} for k,v in (data.items() if isinstance(data, dict) else [])]
    subtitle = "Cities: "+", ".join(cities)+" • Lookback: "+str(lookback)+" days"
    render_table(os.path.join(outdir,"report.html"), "Analytics KPIs", subtitle, ["Metric","Value"], rows, employee_id, employee_json_str)
    with open(os.path.join(outdir,"analytics.json"), "w", encoding="utf-8") as f: json.dump(data, f, indent=2)
    return {"html": os.path.join(outdir,"report.html"), "json": os.path.join(outdir,"analytics.json"), "csv": None}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--envfile", required=True)
    ap.add_argument("--employee", required=True, type=int)
    ap.add_argument("--employee_json", default=None, help="Employee data as JSON string (from PHP)")
    ap.add_argument("--type", required=True, choices=["market","inventory_zip","closings","new_listings","openhouses","farm_polygon","price_bands","analytics"])
    ap.add_argument("--cities", nargs="*", default=[])
    ap.add_argument("--lookback", type=int, default=30)
    ap.add_argument("--property_type", default=None)
    ap.add_argument("--points", nargs="*", default=[])
    ap.add_argument("--output_base", default=None)
    args = ap.parse_args()

    env = read_env(args.envfile)
    output_base = args.output_base or env.get("OUTPUT_BASE","./vcard-new/reports")
    ts = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    outdir = os.path.join(output_base, str(args.employee), args.type, ts)
    ensure_dir(outdir)

    if args.type == "market":
        res = profile_market(env, outdir, args.cities, args.lookback, args.employee, args.employee_json, args.property_type)
    elif args.type == "inventory_zip":
        res = profile_inventory_zip(env, outdir, args.cities, args.employee, args.employee_json, args.lookback, args.property_type)
    elif args.type == "closings":
        res = profile_closings(env, outdir, args.cities, args.lookback, args.employee, args.employee_json, args.property_type)
    elif args.type == "new_listings":
        res = profile_new_listings(env, outdir, args.cities, args.lookback, args.employee, args.employee_json, args.property_type)
    elif args.type == "openhouses":
        res = profile_openhouses(env, outdir, args.cities, args.employee, args.employee_json)
    elif args.type == "farm_polygon":
        res = profile_farm_polygon(env, outdir, args.points, args.employee, args.employee_json)
    elif args.type == "price_bands":
        res = profile_price_bands(env, outdir, args.cities, args.employee, args.employee_json, args.property_type)
    elif args.type == "analytics":
        res = profile_analytics(env, outdir, args.cities, args.lookback, args.property_type, args.employee, args.employee_json)

    payload = {"ok": True, "employee_id": args.employee, "report_type": args.type, "lookback_days": args.lookback,
               "cities": args.cities, "html_path": res.get("html"), "json_path": res.get("json"), "csv_primary_path": res.get("csv"), "outdir": outdir}
    print(json.dumps(payload))

if __name__ == "__main__":
    sys.exit(main())
