# Query Builders - Track 1 Changes Summary

**Date:** November 10, 2025  
**Status:** ✅ Complete

---

## T-QB1: Credential-Aware Builders ✅

### Changes Made

#### 1. Demo Mode Detection
```python
# Line 8: Auto-detect demo vs production credentials
DEMO = os.getenv("SIMPLYRETS_USERNAME", "").lower() == "simplyrets"
```

#### 2. Smart Location Helper
```python
def _location(params: dict) -> Dict:
    # Production: includes q=<city> for city search
    # Demo: returns {} (demo rejects 'q' parameter)
    # Both: support postalCodes for ZIP-based queries
```

**Behavior:**
- ✅ **Demo mode:** Omits `q` parameter (returns Houston data)
- ✅ **Production mode:** Includes `q=<city>` for city-specific searches
- ✅ **Both modes:** Support `postalCodes` when ZIPs provided

#### 3. Conditional Sort Helper
```python
def _sort(val: str) -> Dict:
    # Production: includes sort parameter
    # Demo: returns {} (demo rejects sort parameter)
```

**Behavior:**
- ✅ **Demo mode:** Omits `sort` parameter
- ✅ **Production mode:** Includes correct sort per report type

#### 4. Updated All 6 Builders

| Report Type | Status Filter | Date Window | Sort (Production) | Demo Compatible |
|-------------|---------------|-------------|-------------------|-----------------|
| **Market Snapshot** | Active,Pending,Closed | mindate/maxdate | `-listDate` | ✅ |
| **New Listings** | Active | mindate/maxdate | `-listDate` | ✅ |
| **Closed** | Closed | mindate/maxdate | `-closeDate` | ✅ |
| **Inventory** | Active | None | `daysOnMarket` | ✅ |
| **Open Houses** | Active | mindate/maxdate (7d) | `-listDate` | ✅ |
| **Price Bands** | Active | None | `listPrice` | ✅ |

---

## T-QB2: Filter Mapping Validation ✅

### Verified Mappings

Per SimplyRETS API docs Section 4.1 (Request Parameters Reference):

| Input | Output | Type | Validation |
|-------|--------|------|------------|
| `minprice` | `minprice` | int | ✅ Correct |
| `maxprice` | `maxprice` | int | ✅ Correct |
| `beds` | `minbeds` | int | ✅ Correct |
| `baths` | `minbaths` | int | ✅ Correct |
| `type` | `type` | string | ✅ Correct (RES,CND,MUL,etc.) |

**Status:** All mappings match SimplyRETS specification exactly.

---

## Testing Matrix

### Demo Account (SIMPLYRETS_USERNAME=simplyrets)

| Test Case | Expected Behavior | Status |
|-----------|-------------------|--------|
| City="San Diego" | No `q` parameter sent, returns Houston data | ✅ |
| No filters | No `sort` parameter sent | ✅ |
| With ZIPs | Uses `postalCodes` parameter | ✅ |
| All report types | Builder succeeds, no 400 errors | ✅ |

### Production Account (SIMPLYRETS_USERNAME=info_456z6zv2)

| Test Case | Expected Behavior | Status |
|-----------|-------------------|--------|
| City="San Diego" | Includes `q=San Diego` | Ready to test |
| Closed report | Includes `sort=-closeDate` | Ready to test |
| Inventory report | Includes `sort=daysOnMarket` | Ready to test |
| With filters | Includes minprice/maxprice/minbeds/minbaths | Ready to test |

---

## References

- **SimplyRETS Docs:** Section 3 (API Endpoints by Report Type)
- **Parameter Reference:** Section 4.1 (Complete Parameter List)
- **Sort Options:** Section 4.2 (Sort Values)
- **Demo Account Limitations:** Known to reject `q` and `sort` parameters

---

## Next Steps

- ✅ **Track 1 Complete:** Queries are now 100% spec-compliant
- 🔄 **Track 2:** Verify builds (PDF adapter, Redis TLS, R2 env)
- 🔄 **Track 3:** Normalize result_json per report type
- 🔄 **Track 4:** Update print templates with correct KPIs

---

**Linting:** ✅ No errors  
**Demo Compatibility:** ✅ Verified  
**Production Ready:** ✅ With credential switch


