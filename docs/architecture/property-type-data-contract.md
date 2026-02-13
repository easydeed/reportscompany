# Property Type Data Contract

> Canonical reference for how property types flow through the system:
> **SiteX (assessor data) -> Backend API -> SimplyRETS (MLS data) -> Frontend**

---

## 1. Data Flow Overview

```
Google Places Autocomplete
        |
        v
  Frontend (step-property.tsx)
        | POST /api/proxy/v1/property/search
        v
  Backend API (property.py)
        | calls SiteX Pro API
        v
  SiteX returns PropertyCharacteristics.UseCode
        | mapped to PropertyData.property_type
        v
  Frontend receives property_type, passes to Step 2
        | POST /api/proxy/v1/property/comparables { property_type: "..." }
        v
  Backend API (property.py get_comparables)
        | maps property_type -> SimplyRETS type + subtype params
        v
  SimplyRETS API (/properties?type=...&subtype=...)
        | returns listings filtered by type
        v
  Backend post-filters by property.subType
        | ensures no mismatched types leak through
        v
  Frontend displays comparables
```

---

## 2. SiteX UseCode Values

SiteX's `PropertyCharacteristics.UseCode` comes from county assessor records.
Values are **not standardized** and vary by county. Common values observed:

| SiteX UseCode          | Meaning                     |
|------------------------|-----------------------------|
| `SFR`                  | Single Family Residence     |
| `RSFR`                 | Residential Single Family   |
| `Single Family`        | Single Family Residence     |
| `SingleFamily`         | Single Family Residence     |
| `Single Family Residential` | Single Family Residence |
| `Residential`          | Generic residential (often SFR) |
| `CONDO`                | Condominium                 |
| `Condominium`          | Condominium                 |
| `TOWNHOUSE`            | Townhouse                   |
| `Townhouse`            | Townhouse                   |
| `TH`                   | Townhouse                   |
| `DUPLEX`               | Duplex                      |
| `Duplex`               | Duplex                      |
| `TRIPLEX`              | Triplex                     |
| `QUADPLEX`             | Quadruplex                  |
| `Multi-Family`         | Multi-Family                |
| `MultiFamily`          | Multi-Family                |
| `MOBILE`               | Mobile/Manufactured Home    |
| `MobileHome`           | Mobile/Manufactured Home    |
| `Manufactured`         | Manufactured Home           |
| `LAND`                 | Vacant Land                 |
| `Vacant Land`          | Vacant Land                 |
| `COMMERCIAL`           | Commercial                  |
| `PUD`                  | Planned Unit Development (treat as SFR) |
| *(empty string)*       | Unknown / Not provided      |

**Source:** `apps/api/src/api/services/sitex.py` line 490:
```python
property_type = characteristics.get("UseCode", "") or characteristics.get("PropertyType", "")
```

---

## 3. SimplyRETS API Parameters

Reference: https://docs.simplyrets.com/api/index.html#/Listings/get_properties

### 3a. `type` Parameter (Primary Property Type)

Controls the broad property category. **Case-insensitive in the query.**

| SimplyRETS `type` value | Description                                |
|-------------------------|--------------------------------------------|
| `residential`           | All residential (SFR, condo, townhouse, etc.) |
| `condominium`           | Condominiums specifically                  |
| `multifamily`           | Multi-family (duplex, triplex, etc.)       |
| `mobilehome`            | Mobile/manufactured homes                  |
| `land`                  | Vacant land                                |
| `farm`                  | Farm/ranch                                 |
| `commercial`            | Commercial property                        |
| `commerciallease`       | Commercial lease                           |
| `rental`                | Rental listings                            |

> **Important:** `type=residential` returns ALL residential subtypes mixed together
> (SFR, condos, townhouses). You MUST also use `subtype` to narrow it down.

### 3b. `subtype` Parameter (Property Sub-Type)

Narrows within a `type`. These are the values relevant to residential:

| SimplyRETS `subtype` value | Description                       |
|----------------------------|-----------------------------------|
| `singlefamilyresidence`    | Single Family Residence           |
| `condominium`              | Condominium                       |
| `townhouse`                | Townhouse                         |
| `duplex`                   | Duplex                            |
| `triplex`                  | Triplex                           |
| `quadruplex`               | Quadruplex                        |
| `manufacturedhome`         | Manufactured/Mobile Home          |
| `manufacturedonland`       | Manufactured on land              |
| `apartment`                | Apartment                         |
| `stockcooperative`         | Co-op                             |

> **Note:** Per SimplyRETS docs, "not all sub type filters are available for all vendors."

### 3c. Response Fields for Property Type

Each SimplyRETS listing includes:
```json
{
  "property": {
    "type": "RES",           // e.g., "RES", "CND", "MLF"
    "subType": "Single Family Residence",  // human-readable
    "subTypeText": "LST_SUBCOND_36"        // vendor-specific code
  }
}
```

Known `property.subType` response values:
| Response `property.subType`   | Category        |
|-------------------------------|-----------------|
| `Single Family Residence`     | SFR             |
| `Condominium`                 | Condo           |
| `Townhouse`                   | Townhouse       |
| `Duplex`                      | Duplex          |
| `Triplex`                     | Triplex         |
| `Quadruplex`                  | Quadruplex      |
| `Manufactured Home`           | Mobile Home     |
| `Stock Cooperative`           | Co-op           |

---

## 4. Canonical Mapping: SiteX -> SimplyRETS

This is the **authoritative mapping** used by `apps/api/src/api/routes/property.py`:

```python
PROPERTY_TYPE_MAP = {
    # ---- Single Family Residence ----
    "sfr":                          ("residential", "singlefamilyresidence"),
    "rsfr":                         ("residential", "singlefamilyresidence"),
    "single family":                ("residential", "singlefamilyresidence"),
    "singlefamily":                 ("residential", "singlefamilyresidence"),
    "single family residential":    ("residential", "singlefamilyresidence"),
    "residential":                  ("residential", "singlefamilyresidence"),
    "pud":                          ("residential", "singlefamilyresidence"),

    # ---- Condominium ----
    "condo":                        ("condominium", "condominium"),
    "condominium":                  ("condominium", "condominium"),

    # ---- Townhouse ----
    "townhouse":                    ("residential", "townhouse"),
    "th":                           ("residential", "townhouse"),
    "townhome":                     ("residential", "townhouse"),

    # ---- Duplex ----
    "duplex":                       ("multifamily", "duplex"),

    # ---- Triplex ----
    "triplex":                      ("multifamily", "triplex"),

    # ---- Quadruplex ----
    "quadplex":                     ("multifamily", "quadruplex"),
    "quadruplex":                   ("multifamily", "quadruplex"),

    # ---- Multi-Family (generic) ----
    "multi-family":                 ("multifamily", None),
    "multifamily":                  ("multifamily", None),

    # ---- Mobile / Manufactured ----
    "mobile":                       ("mobilehome", "manufacturedhome"),
    "mobilehome":                   ("mobilehome", "manufacturedhome"),
    "manufactured":                 ("mobilehome", "manufacturedhome"),

    # ---- Land ----
    "land":                         ("land", None),
    "vacant land":                  ("land", None),

    # ---- Commercial ----
    "commercial":                   ("commercial", None),
}
```

**Lookup logic:**
1. Lowercase the SiteX `UseCode`
2. Try exact match in `PROPERTY_TYPE_MAP`
3. If no exact match, try substring matching (e.g., "sfr" in value)
4. If still no match, default to `("residential", "singlefamilyresidence")`

---

## 5. Post-Filter Contract

Even with correct `type` + `subtype` query params, SimplyRETS may return
mixed results (vendor-dependent). A **post-filter** is required as a safety net.

### Post-filter rules:

| Subject Type (normalized) | Allow in results (by `property.subType`) |
|---------------------------|------------------------------------------|
| SFR                       | `Single Family Residence`, `null/empty`  |
| Condo                     | `Condominium`, `Stock Cooperative`       |
| Townhouse                 | `Townhouse`                              |
| Duplex                    | `Duplex`                                 |
| Triplex                   | `Triplex`                                |
| Quadruplex                | `Quadruplex`                             |
| Mobile Home               | `Manufactured Home`                      |
| Multi-Family (generic)    | `Duplex`, `Triplex`, `Quadruplex`        |

**Implementation:** After SimplyRETS returns listings, filter by checking
`listing["property"]["subType"]` against the allowed set for the subject's type.

---

## 6. Normalized Property Type Enum

Internal canonical values used throughout the system:

```python
class NormalizedPropertyType(str, Enum):
    SFR = "sfr"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    DUPLEX = "duplex"
    TRIPLEX = "triplex"
    QUADRUPLEX = "quadruplex"
    MULTIFAMILY = "multifamily"
    MOBILE_HOME = "mobile_home"
    LAND = "land"
    COMMERCIAL = "commercial"
    UNKNOWN = "unknown"
```

---

## 7. Files Involved

| File | Role |
|------|------|
| `apps/api/src/api/services/sitex.py` | Extracts `UseCode` from SiteX response |
| `apps/api/src/api/routes/property.py` | Maps UseCode -> SimplyRETS params, post-filters results |
| `apps/api/src/api/services/simplyrets.py` | Sends query to SimplyRETS, normalizes response |
| `apps/web/components/property-wizard/property-wizard.tsx` | Passes `property_type` from Step 1 to comparables request |
| `apps/web/components/property-wizard/step-property.tsx` | Displays property type from SiteX |
| `apps/web/components/property-wizard/types.ts` | Frontend `PropertyData` interface |

---

## 8. Changelog

| Date       | Change |
|------------|--------|
| 2026-02-13 | Initial contract created. Identified that property type filter was not being applied due to SiteX UseCode mismatch with SimplyRETS params. |
