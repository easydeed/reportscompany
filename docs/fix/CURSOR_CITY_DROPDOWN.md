# Cursor Prompt: Replace City Search With CRMLS City Dropdown

## Task

Replace the free-text city search input in the unified wizard's area selection (`step-where-when.tsx`) with a **searchable dropdown/combobox** populated from a static list of all cities covered by CRMLS in the 6 Southern California counties.

This eliminates spelling errors, invalid city names, and zero-result queries.

---

## What to Build

### 1. Create the City List Data File

Create `apps/web/lib/crmls-cities.ts` containing every city in the 6 Southern California counties that CRMLS covers.

**Counties to include:**
- Los Angeles County
- Orange County
- Riverside County
- San Bernardino County
- Ventura County
- San Diego County

**Data structure:**

```typescript
export interface CRMLSCity {
  city: string;        // e.g., "Los Angeles"
  county: string;      // e.g., "Los Angeles County"
  state: string;       // always "CA"
  label: string;       // display: "Los Angeles, CA"
  searchTerms: string; // lowercase for fast search: "los angeles ca los angeles county"
}

export const CRMLS_CITIES: CRMLSCity[] = [
  // Los Angeles County (~90 cities)
  { city: "Agoura Hills", county: "Los Angeles County", state: "CA", label: "Agoura Hills, CA", searchTerms: "agoura hills ca los angeles county" },
  { city: "Alhambra", county: "Los Angeles County", state: "CA", label: "Alhambra, CA", searchTerms: "alhambra ca los angeles county" },
  { city: "Arcadia", county: "Los Angeles County", state: "CA", label: "Arcadia, CA", searchTerms: "arcadia ca los angeles county" },
  { city: "Artesia", county: "Los Angeles County", state: "CA", label: "Artesia, CA", searchTerms: "artesia ca los angeles county" },
  { city: "Azusa", county: "Los Angeles County", state: "CA", label: "Azusa, CA", searchTerms: "azusa ca los angeles county" },
  { city: "Baldwin Park", county: "Los Angeles County", state: "CA", label: "Baldwin Park, CA", searchTerms: "baldwin park ca los angeles county" },
  { city: "Bell", county: "Los Angeles County", state: "CA", label: "Bell, CA", searchTerms: "bell ca los angeles county" },
  { city: "Bell Gardens", county: "Los Angeles County", state: "CA", label: "Bell Gardens, CA", searchTerms: "bell gardens ca los angeles county" },
  { city: "Bellflower", county: "Los Angeles County", state: "CA", label: "Bellflower, CA", searchTerms: "bellflower ca los angeles county" },
  { city: "Beverly Hills", county: "Los Angeles County", state: "CA", label: "Beverly Hills, CA", searchTerms: "beverly hills ca los angeles county" },
  { city: "Bradbury", county: "Los Angeles County", state: "CA", label: "Bradbury, CA", searchTerms: "bradbury ca los angeles county" },
  { city: "Burbank", county: "Los Angeles County", state: "CA", label: "Burbank, CA", searchTerms: "burbank ca los angeles county" },
  { city: "Calabasas", county: "Los Angeles County", state: "CA", label: "Calabasas, CA", searchTerms: "calabasas ca los angeles county" },
  // ... CONTINUE FOR ALL CITIES
  // You MUST include every incorporated city in all 6 counties.
  // Use official U.S. Census Bureau incorporated places for each county.
  // Also include major unincorporated communities that appear in MLS data
  // (e.g., Altadena, East Los Angeles, Hacienda Heights, La Crescenta,
  //  Rowland Heights, Walnut Park, West Hollywood is incorporated,
  //  Marina del Rey is unincorporated, etc.)
];

// County groups for optional county-level filtering
export const CRMLS_COUNTIES = [
  "Los Angeles County",
  "Orange County",
  "Riverside County",
  "San Bernardino County",
  "Ventura County",
  "San Diego County",
] as const;

// Quick lookup set for validation
export const VALID_CITY_NAMES = new Set(CRMLS_CITIES.map(c => c.city));
```

**CRITICAL: Be thorough.** This list must include:

**Los Angeles County** (88 incorporated cities + major unincorporated areas):
Agoura Hills, Alhambra, Arcadia, Artesia, Avalon, Azusa, Baldwin Park, Bell, Bell Gardens, Bellflower, Beverly Hills, Bradbury, Burbank, Calabasas, Carson, Cerritos, Claremont, Commerce, Compton, Covina, Cudahy, Culver City, Diamond Bar, Downey, Duarte, El Monte, El Segundo, Gardena, Glendale, Glendora, Hawaiian Gardens, Hawthorne, Hermosa Beach, Hidden Hills, Huntington Park, Industry, Inglewood, Irwindale, La Cañada Flintridge, La Habra Heights, La Mirada, La Puente, La Verne, Lakewood, Lancaster, Lawndale, Lomita, Long Beach, Los Angeles, Lynwood, Malibu, Manhattan Beach, Maywood, Monrovia, Montebello, Monterey Park, Norwalk, Palmdale, Palos Verdes Estates, Paramount, Pasadena, Pico Rivera, Pomona, Rancho Palos Verdes, Redondo Beach, Rolling Hills, Rolling Hills Estates, Rosemead, San Dimas, San Fernando, San Gabriel, San Marino, Santa Clarita, Santa Fe Springs, Santa Monica, Sierra Madre, Signal Hill, South El Monte, South Gate, South Pasadena, Temple City, Torrance, Vernon, Walnut, West Covina, West Hollywood, Westlake Village, Whittier.

Plus unincorporated areas commonly used in MLS: Altadena, East Los Angeles, Hacienda Heights, La Crescenta-Montrose, Marina del Rey, Rowland Heights, Topanga, View Park-Windsor Hills, West Carson, Willowbrook, and others that appear in your SimplyRETS data.

**Orange County** (34 cities):
Aliso Viejo, Anaheim, Brea, Buena Park, Costa Mesa, Cypress, Dana Point, Fountain Valley, Fullerton, Garden Grove, Huntington Beach, Irvine, La Habra, La Palma, Laguna Beach, Laguna Hills, Laguna Niguel, Laguna Woods, Lake Forest, Los Alamitos, Mission Viejo, Newport Beach, Orange, Placentia, Rancho Santa Margarita, San Clemente, San Juan Capistrano, Santa Ana, Seal Beach, Stanton, Tustin, Villa Park, Westminster, Yorba Linda.

**Riverside County** (28 cities):
Banning, Beaumont, Blythe, Calimesa, Canyon Lake, Cathedral City, Coachella, Corona, Desert Hot Springs, Eastvale, Hemet, Indian Wells, Indio, Jurupa Valley, La Quinta, Lake Elsinore, Menifee, Moreno Valley, Murrieta, Norco, Palm Desert, Palm Springs, Perris, Rancho Mirage, Riverside, San Jacinto, Temecula, Wildomar.

Plus unincorporated: Bermuda Dunes, French Valley, Good Hope, Lake Mathews, Lakeland Village, Mead Valley, Sun City, Temescal Valley, Thermal, Thousand Palms, Winchester.

**San Bernardino County** (24 cities):
Adelanto, Apple Valley, Barstow, Big Bear Lake, Chino, Chino Hills, Colton, Fontana, Grand Terrace, Hesperia, Highland, Loma Linda, Montclair, Needles, Ontario, Rancho Cucamonga, Redlands, Rialto, San Bernardino, Twentynine Palms, Upland, Victorville, Yucaipa, Yucca Valley.

Plus unincorporated: Bloomington, Crestline, Devore, Lake Arrowhead, Lucerne Valley, Lytle Creek, Muscoy, Oak Hills, Phelan, Running Springs.

**Ventura County** (10 cities):
Camarillo, Fillmore, Moorpark, Ojai, Oxnard, Port Hueneme, San Buenaventura (Ventura), Santa Paula, Simi Valley, Thousand Oaks.

Plus unincorporated: Bell Canyon, Casa Conejo, Channel Islands Beach, El Rio, Meiners Oaks, Mira Monte, Newbury Park, Oak Park, Oak View, Piru, Somis.

**San Diego County** (18 cities):
Carlsbad, Chula Vista, Coronado, Del Mar, El Cajon, Encinitas, Escondido, Imperial Beach, La Mesa, Lemon Grove, National City, Oceanside, Poway, San Diego, San Marcos, Santee, Solana Beach, Vista.

Plus unincorporated: Alpine, Bonita, Bonsall, Borrego Springs, Cardiff-by-the-Sea, Fallbrook, Jamul, Lakeside, Ramona, Rancho San Diego, Rancho Santa Fe, San Ysidro, Spring Valley, Valley Center, Winter Gardens.

---

### 2. Build the Searchable City Combobox Component

Create `apps/web/components/shared/city-combobox.tsx`

**Behavior:**
- Uses shadcn/ui `Combobox` pattern (Popover + Command)
- Agent types → results filter in real time (client-side, no API calls)
- Search matches against city name, county, and label (fuzzy-friendly)
- Results grouped by county with county name as a subtle section header
- Show max 20 results at a time (performance)
- Selected city highlights and popover closes
- Clear button to reset selection
- Shows county in muted text next to city name: "Glendale, CA · Los Angeles County"

**Component interface:**

```typescript
interface CityComboboxProps {
  value: string | null;           // selected city name
  onChange: (city: CRMLSCity | null) => void;
  placeholder?: string;           // default: "Search for a city..."
  recentCities?: string[];        // city names from recent reports
  disabled?: boolean;
}
```

**Search algorithm:**

```typescript
function filterCities(query: string): CRMLSCity[] {
  if (!query || query.length < 2) return [];
  
  const q = query.toLowerCase().trim();
  
  // Exact prefix match on city name gets priority
  const exactPrefix = CRMLS_CITIES.filter(c => 
    c.city.toLowerCase().startsWith(q)
  );
  
  // Then fuzzy match on searchTerms
  const fuzzy = CRMLS_CITIES.filter(c => 
    c.searchTerms.includes(q) && !c.city.toLowerCase().startsWith(q)
  );
  
  return [...exactPrefix, ...fuzzy].slice(0, 20);
}
```

**Recent cities section:**
If `recentCities` is provided, show them as clickable pills ABOVE the search input:
```
Recent: [Los Angeles] [Beverly Hills] [Glendale]
```
Clicking a recent city selects it immediately without opening the dropdown.

**Visual design:**
- Match the existing wizard styling (shadcn/ui, Tailwind)
- Input has a search icon (magnifying glass) on the left
- Dropdown items show: City Name on the left, County in muted text on the right
- Selected item shows a checkmark
- Grouped by county with subtle divider and county label

---

### 3. Wire Into the Unified Wizard

**File to modify:** `apps/web/components/unified-wizard/step-where-when.tsx`

**Replace the current city input:**

```typescript
// BEFORE (Google Places autocomplete or free text):
<Input 
  placeholder="Search for a city..."
  value={city}
  onChange={handleCityChange}
/>

// AFTER (searchable dropdown):
import { CityCombobox } from '@/components/shared/city-combobox';

<CityCombobox
  value={selectedCity}
  onChange={(city) => {
    setSelectedCity(city?.city || null);
    // Update wizard state
    updateState({ city: city?.city || null });
  }}
  recentCities={recentCities}
  placeholder="Search for a city..."
/>
```

**Also update the schedule builder if it still has its own area section.**
Check `apps/web/components/schedule-builder/sections/area-section.tsx` — if this file is still in use (for edit mode or fallback), update it to use the same `CityCombobox`.

**Also update the report builder v0 if it still exists.**
Check `apps/web/components/v0-report-builder/step-area.tsx` — if this is still mounted anywhere, update it too.

---

### 4. Add City Validation on the Backend

**File to modify:** `apps/api/src/api/routes/schedules.py` and `apps/api/src/api/routes/reports.py`

Add server-side validation that the submitted city name exists in the CRMLS city list. This catches any edge cases where the frontend is bypassed.

```python
from worker.crmls_cities import VALID_CITY_NAMES  # or a shared constants file

# In the schedule/report create endpoint:
if request.city and request.city not in VALID_CITY_NAMES:
    raise HTTPException(
        status_code=422,
        detail=f"'{request.city}' is not a recognized CRMLS city. "
               f"Please select a city from the dropdown."
    )
```

Create a matching Python file: `apps/worker/src/worker/crmls_cities.py` (or `apps/api/src/api/crmls_cities.py`) with the same city list as a Python set:

```python
VALID_CITY_NAMES = {
    "Agoura Hills", "Alhambra", "Arcadia", "Artesia", ...
}
```

This ensures frontend and backend are in sync. Both read from their own copy of the same canonical list.

---

### 5. Remove Google Places Dependency (for city search)

If the city search was previously using Google Places autocomplete:
- Remove the Google Places API call from the area selection step
- Keep Google Places ONLY for the property wizard address search (that's a different use case — street-level geocoding)
- This saves API costs — no more Places API calls for city selection

**Do NOT remove:**
- `useGooglePlaces` hook if it's used elsewhere (property wizard)
- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` — still needed for property address search and map components

---

### 6. Handle Edge Cases

**City name variations:**
Some cities have alternate names or spellings in MLS data. Add aliases:

```typescript
// In crmls-cities.ts, add common aliases to searchTerms:
{
  city: "San Buenaventura (Ventura)",
  searchTerms: "san buenaventura ventura ca ventura county",
  // Agent types "Ventura" → finds this entry
}
```

Common aliases to include:
- "Ventura" → "San Buenaventura (Ventura)"
- "Rancho PV" → "Rancho Palos Verdes"  
- "RPV" → "Rancho Palos Verdes"
- "PV Estates" → "Palos Verdes Estates"
- "DTLA" → "Los Angeles" (add to searchTerms)
- "WeHo" → "West Hollywood"
- "HB" → "Huntington Beach"
- "OC" → should surface all Orange County cities
- "IE" → should surface Riverside + San Bernardino county cities (Inland Empire)

```typescript
// Example with aliases:
{ 
  city: "Rancho Palos Verdes", 
  county: "Los Angeles County", 
  state: "CA", 
  label: "Rancho Palos Verdes, CA", 
  searchTerms: "rancho palos verdes rpv ca los angeles county south bay" 
},
```

**0-result handling:**
If the agent types something that matches no cities, show:
"No cities found. Try a different spelling or search by ZIP code instead."

**ZIP mode unchanged:**
The ZIP code entry (multi-tag input, up to 5 ZIPs) stays exactly as-is. This change only affects the City mode.

---

## Testing

After implementation, verify:

1. **Search works:** Type "Glen" → shows Glendale, Glendora, Glen Avon
2. **County grouping:** Results from different counties show county headers
3. **Fuzzy search:** Type "beverly" → shows Beverly Hills
4. **Alias search:** Type "WeHo" → shows West Hollywood
5. **County search:** Type "orange county" → shows all OC cities
6. **Recent cities:** Previously used cities appear as pills above the search
7. **Selection:** Click a city → popover closes, city name populates, wizard state updates
8. **Clear:** Click clear → city resets, wizard state clears
9. **Preview updates:** Selecting a city updates the sidebar preview header title
10. **Submit works:** Schedule/report created with correct city name matching SimplyRETS `cities` parameter
11. **Validation:** Submitting an invalid city via API returns 422 error
12. **Mobile:** Dropdown works on mobile (full-width, touch-friendly)
13. **Performance:** Typing is instant — no lag on 400+ city list (client-side filtering only)

---

## Files to Create

```
apps/web/lib/crmls-cities.ts                    ← Full city list (300-400 entries)
apps/web/components/shared/city-combobox.tsx     ← Searchable dropdown component
apps/api/src/api/crmls_cities.py                 ← Python validation set (or shared location)
```

## Files to Modify

```
apps/web/components/unified-wizard/step-where-when.tsx  ← Use CityCombobox
apps/web/components/schedule-builder/sections/area-section.tsx  ← Use CityCombobox (if still in use)
apps/web/components/v0-report-builder/step-area.tsx  ← Use CityCombobox (if still in use)
apps/api/src/api/routes/schedules.py  ← Add city validation
apps/api/src/api/routes/reports.py    ← Add city validation
```
