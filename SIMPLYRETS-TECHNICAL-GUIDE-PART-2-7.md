# SimplyRETS Real Estate Report System - Complete Technical Guide (Part 2-7)

**Document Version**: 1.0  
**Last Updated**: October 31, 2025  
**Continuation of**: SIMPLYRETS-COMPLETE-TECHNICAL-GUIDE.md

---

## Part 2: Data Processing Pipeline

---

## 7. Data Extraction & Transformation

### 7.1 Data Flow Overview

```
SimplyRETS API → Raw JSON → Data Extraction → Transformation → Aggregation → Report Generation
```

### 7.2 Data Extraction Pipeline

**File**: `vcard-new/reports/core-system/data_extractor.py`

```python
import json
from datetime import datetime
from typing import List, Dict, Any

class PropertyDataExtractor:
    """
    Extract and normalize property data from SimplyRETS API responses.
    """
    
    def __init__(self, raw_properties: List[Dict]):
        self.raw_properties = raw_properties
        self.extracted_data = []
    
    def extract_all(self):
        """
        Extract all properties.
        
        Returns:
            list: Normalized property objects
        """
        for prop in self.raw_properties:
            extracted = self.extract_single(prop)
            if extracted:
                self.extracted_data.append(extracted)
        
        return self.extracted_data
    
    def extract_single(self, property_obj: Dict) -> Dict:
        """
        Extract and normalize a single property.
        
        Args:
            property_obj (dict): Raw property object from API
        
        Returns:
            dict: Normalized property data
        """
        try:
            # Core identifiers
            mls_id = property_obj.get('mlsId')
            listing_id = property_obj.get('listingId', mls_id)
            
            # Dates
            list_date = self._parse_date(property_obj.get('listDate'))
            close_date = self._parse_date(property_obj.get('sales', {}).get('closeDate'))
            modified_date = self._parse_date(property_obj.get('modified'))
            
            # Prices
            list_price = self._safe_int(property_obj.get('listPrice'))
            close_price = self._safe_int(property_obj.get('sales', {}).get('closePrice'))
            original_list_price = self._safe_int(property_obj.get('mls', {}).get('originalListPrice'))
            
            # Address
            address_obj = property_obj.get('address', {})
            full_address = address_obj.get('full', '')
            street_number = str(address_obj.get('streetNumber', ''))
            street_name = address_obj.get('streetName', '')
            street_suffix = address_obj.get('streetSuffix', '')
            unit = address_obj.get('unit')
            city = address_obj.get('city', '')
            state = address_obj.get('state', '')
            zip_code = address_obj.get('postalCode', '')
            
            # Property details
            property_obj_details = property_obj.get('property', {})
            bedrooms = self._safe_int(property_obj_details.get('bedrooms'))
            bathrooms = self._safe_float(property_obj_details.get('bathrooms'))
            baths_full = self._safe_int(property_obj_details.get('bathsFull'))
            baths_half = self._safe_int(property_obj_details.get('bathsHalf'))
            sqft = self._safe_int(property_obj_details.get('area'))
            lot_size = self._safe_int(property_obj_details.get('lotSize'))
            year_built = self._safe_int(property_obj_details.get('yearBuilt'))
            property_type = property_obj_details.get('type', 'RES')
            property_subtype = property_obj_details.get('subType', '')
            stories = self._safe_int(property_obj_details.get('stories'))
            garage_spaces = self._safe_int(property_obj_details.get('garageSpaces'))
            
            # MLS information
            mls_obj = property_obj.get('mls', {})
            status = mls_obj.get('status', 'Unknown')
            days_on_market = self._safe_int(property_obj.get('daysOnMarket', 0))
            mls_area = mls_obj.get('area', '')
            mls_status_text = mls_obj.get('statusText', status)
            
            # Geo data
            geo_obj = property_obj.get('geo', {})
            latitude = self._safe_float(geo_obj.get('lat'))
            longitude = self._safe_float(geo_obj.get('lng'))
            county = geo_obj.get('county', '')
            
            # Agent/Office (optional)
            agent_obj = property_obj.get('agent', {})
            agent_name = f"{agent_obj.get('firstName', '')} {agent_obj.get('lastName', '')}".strip()
            agent_email = agent_obj.get('email', '')
            agent_phone = agent_obj.get('contact', '')
            
            office_obj = property_obj.get('office', {})
            office_name = office_obj.get('name', '')
            
            # Photos
            photos = property_obj.get('photos', [])
            primary_photo = photos[0] if photos else None
            
            # Open houses
            open_houses = property_obj.get('openHouse', [])
            has_open_house = len(open_houses) > 0
            
            # Calculated fields
            price_per_sqft = None
            if list_price and sqft and sqft > 0:
                price_per_sqft = round(list_price / sqft, 2)
            
            close_to_list_ratio = None
            if close_price and list_price and list_price > 0:
                close_to_list_ratio = round((close_price / list_price) * 100, 2)
            
            # Build normalized object
            normalized = {
                # Identifiers
                'mls_id': mls_id,
                'listing_id': listing_id,
                
                # Dates
                'list_date': list_date,
                'close_date': close_date,
                'modified_date': modified_date,
                
                # Prices
                'list_price': list_price,
                'close_price': close_price,
                'original_list_price': original_list_price,
                'price_per_sqft': price_per_sqft,
                
                # Address
                'full_address': full_address,
                'street_number': street_number,
                'street_name': street_name,
                'street_suffix': street_suffix,
                'unit': unit,
                'city': city,
                'state': state,
                'zip_code': zip_code,
                
                # Property details
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'baths_full': baths_full,
                'baths_half': baths_half,
                'sqft': sqft,
                'lot_size': lot_size,
                'year_built': year_built,
                'property_type': property_type,
                'property_subtype': property_subtype,
                'stories': stories,
                'garage_spaces': garage_spaces,
                
                # MLS info
                'status': status,
                'days_on_market': days_on_market,
                'mls_area': mls_area,
                'mls_status_text': mls_status_text,
                
                # Geo
                'latitude': latitude,
                'longitude': longitude,
                'county': county,
                
                # Agent/Office
                'agent_name': agent_name,
                'agent_email': agent_email,
                'agent_phone': agent_phone,
                'office_name': office_name,
                
                # Media
                'primary_photo': primary_photo,
                'photo_count': len(photos),
                
                # Features
                'has_open_house': has_open_house,
                'open_house_count': len(open_houses),
                
                # Calculated
                'close_to_list_ratio': close_to_list_ratio,
                
                # Original (for debugging)
                '_original': property_obj if __debug__ else None
            }
            
            return normalized
            
        except Exception as e:
            print(f"Error extracting property {property_obj.get('mlsId')}: {str(e)}")
            return None
    
    # Helper methods
    def _parse_date(self, date_string):
        """Parse ISO date string to datetime object"""
        if not date_string:
            return None
        try:
            # Handle ISO format: 2024-10-15T00:00:00.000Z
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            return None
    
    def _safe_int(self, value, default=None):
        """Safely convert to int"""
        if value is None:
            return default
        try:
            return int(value)
        except:
            return default
    
    def _safe_float(self, value, default=None):
        """Safely convert to float"""
        if value is None:
            return default
        try:
            return float(value)
        except:
            return default

# Usage
extractor = PropertyDataExtractor(raw_api_response)
normalized_properties = extractor.extract_all()
print(f"Extracted {len(normalized_properties)} properties")
```

### 7.3 Data Validation

```python
from typing import List, Dict, Optional
from datetime import datetime

class PropertyValidator:
    """
    Validate extracted property data.
    """
    
    @staticmethod
    def validate_property(property_data: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate a single property.
        
        Args:
            property_data (dict): Normalized property data
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Required fields
        required_fields = ['mls_id', 'city', 'list_price', 'status']
        for field in required_fields:
            if not property_data.get(field):
                return False, f"Missing required field: {field}"
        
        # Price validation
        list_price = property_data.get('list_price')
        if list_price and list_price < 0:
            return False, "List price cannot be negative"
        
        if list_price and list_price > 100000000:  # $100M cap
            return False, "List price exceeds reasonable maximum"
        
        # Property size validation
        sqft = property_data.get('sqft')
        if sqft and sqft < 100:
            return False, "Square footage too small"
        
        if sqft and sqft > 50000:
            return False, "Square footage exceeds reasonable maximum"
        
        # Bedroom/bathroom validation
        bedrooms = property_data.get('bedrooms')
        if bedrooms and bedrooms > 20:
            return False, "Bedroom count exceeds reasonable maximum"
        
        bathrooms = property_data.get('bathrooms')
        if bathrooms and bathrooms > 20:
            return False, "Bathroom count exceeds reasonable maximum"
        
        # Date validation
        list_date = property_data.get('list_date')
        if list_date:
            if list_date > datetime.now():
                return False, "List date cannot be in the future"
            
            if list_date.year < 1900:
                return False, "List date is too old"
        
        # Status validation
        valid_statuses = ['Active', 'Pending', 'Closed', 'Expired', 'Withdrawn', 'Temp Off Market']
        if property_data.get('status') not in valid_statuses:
            return False, f"Invalid status: {property_data.get('status')}"
        
        return True, None
    
    @staticmethod
    def validate_batch(properties: List[Dict]) -> Dict:
        """
        Validate a batch of properties.
        
        Args:
            properties (list): List of normalized property data
        
        Returns:
            dict: Validation results
        """
        valid_properties = []
        invalid_properties = []
        validation_errors = []
        
        for prop in properties:
            is_valid, error_msg = PropertyValidator.validate_property(prop)
            
            if is_valid:
                valid_properties.append(prop)
            else:
                invalid_properties.append({
                    'property': prop,
                    'error': error_msg
                })
                validation_errors.append(error_msg)
        
        return {
            'valid': valid_properties,
            'invalid': invalid_properties,
            'valid_count': len(valid_properties),
            'invalid_count': len(invalid_properties),
            'errors': validation_errors
        }

# Usage
validation_results = PropertyValidator.validate_batch(normalized_properties)
print(f"Valid: {validation_results['valid_count']}, Invalid: {validation_results['invalid_count']}")

if validation_results['invalid_count'] > 0:
    print("Validation errors:")
    for error in set(validation_results['errors']):
        print(f"  - {error}")

# Use only valid properties
clean_properties = validation_results['valid']
```

---

## 8. Calculations & Aggregations

### 8.1 Market Statistics Calculations

**File**: `vcard-new/reports/core-system/calculations.py`

```python
import statistics
from typing import List, Dict
from datetime import datetime, timedelta

class MarketCalculator:
    """
    Calculate market statistics from property data.
    """
    
    def __init__(self, properties: List[Dict]):
        self.properties = properties
    
    def calculate_market_snapshot(self) -> Dict:
        """
        Calculate comprehensive market snapshot metrics.
        
        Returns:
            dict: Market statistics
        """
        # Filter by status
        active = [p for p in self.properties if p['status'] == 'Active']
        pending = [p for p in self.properties if p['status'] == 'Pending']
        closed = [p for p in self.properties if p['status'] == 'Closed']
        
        # Count metrics
        total_active = len(active)
        total_pending = len(pending)
        total_closed = len(closed)
        
        # Price metrics
        median_list_price = self._median([p['list_price'] for p in active if p['list_price']]) if active else 0
        median_close_price = self._median([p['close_price'] for p in closed if p['close_price']]) if closed else 0
        avg_list_price = self._average([p['list_price'] for p in active if p['list_price']]) if active else 0
        
        # DOM metrics
        avg_dom = self._average([p['days_on_market'] for p in self.properties if p['days_on_market'] is not None])
        median_dom = self._median([p['days_on_market'] for p in self.properties if p['days_on_market'] is not None])
        
        # Price per sqft
        avg_price_per_sqft = self._average([p['price_per_sqft'] for p in active if p.get('price_per_sqft')])
        
        # Close to list ratio
        close_to_list_ratios = [p['close_to_list_ratio'] for p in closed if p.get('close_to_list_ratio')]
        avg_close_to_list = self._average(close_to_list_ratios) if close_to_list_ratios else 100.0
        
        # New listings (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        new_listings = [p for p in self.properties if p.get('list_date') and p['list_date'] >= seven_days_ago]
        
        # Months of inventory
        # MOI = Active Listings / (Closed Sales / Period in Months)
        # For 30 days: MOI = Active / (Closed / 1)
        moi = round(total_active / total_closed, 2) if total_closed > 0 else 999.0
        
        # Absorption rate (what % of inventory sells per month)
        absorption_rate = round((total_closed / total_active * 100), 2) if total_active > 0 else 0.0
        
        return {
            # Counts
            'total_active': total_active,
            'total_pending': total_pending,
            'total_closed': total_closed,
            'new_listings_7d': len(new_listings),
            
            # Prices
            'median_list_price': round(median_list_price) if median_list_price else 0,
            'median_close_price': round(median_close_price) if median_close_price else 0,
            'avg_list_price': round(avg_list_price) if avg_list_price else 0,
            'avg_price_per_sqft': round(avg_price_per_sqft) if avg_price_per_sqft else 0,
            
            # Time on market
            'avg_dom': round(avg_dom, 1) if avg_dom else 0,
            'median_dom': round(median_dom) if median_dom else 0,
            
            # Market health
            'close_to_list_ratio': round(avg_close_to_list, 1),
            'months_of_inventory': moi,
            'absorption_rate': absorption_rate
        }
    
    def calculate_price_bands(self, bands: List[Dict]) -> List[Dict]:
        """
        Calculate statistics for each price band.
        
        Args:
            bands (list): List of price band definitions
                [{'name': '$500K-$750K', 'min': 500000, 'max': 750000}, ...]
        
        Returns:
            list: Price band statistics
        """
        results = []
        total_count = len(self.properties)
        
        for band in bands:
            # Filter properties in this band
            in_band = [p for p in self.properties 
                      if band['min'] <= p.get('list_price', 0) < band['max']]
            
            count = len(in_band)
            
            if count > 0:
                # Calculate metrics
                median_price = self._median([p['list_price'] for p in in_band])
                avg_dom = self._average([p['days_on_market'] for p in in_band if p['days_on_market']])
                avg_ppsf = self._average([p['price_per_sqft'] for p in in_band if p.get('price_per_sqft')])
                
                # Determine inventory level
                if count >= 100:
                    inventory_level = 'Very High'
                elif count >= 50:
                    inventory_level = 'High'
                elif count >= 20:
                    inventory_level = 'Moderate'
                else:
                    inventory_level = 'Low'
                
                results.append({
                    'band': band['name'],
                    'count': count,
                    'percent': round((count / total_count) * 100, 1) if total_count > 0 else 0,
                    'medianPrice': round(median_price),
                    'avgDOM': round(avg_dom, 1) if avg_dom else 0,
                    'avgPPSF': round(avg_ppsf) if avg_ppsf else 0,
                    'inventory': inventory_level
                })
        
        return results
    
    def calculate_by_property_type(self) -> List[Dict]:
        """
        Calculate metrics grouped by property type.
        
        Returns:
            list: Statistics per property type
        """
        # Group by type
        by_type = {}
        for prop in self.properties:
            prop_type = prop.get('property_type', 'Unknown')
            if prop_type not in by_type:
                by_type[prop_type] = []
            by_type[prop_type].append(prop)
        
        results = []
        for prop_type, props in by_type.items():
            closed_props = [p for p in props if p['status'] == 'Closed']
            
            if closed_props:
                median_price = self._median([p['close_price'] for p in closed_props if p.get('close_price')])
                count = len(closed_props)
                avg_dom = self._average([p['days_on_market'] for p in closed_props if p.get('days_on_market')])
                
                results.append({
                    'type': prop_type,
                    'type_name': self._get_type_name(prop_type),
                    'count': count,
                    'median_price': round(median_price) if median_price else 0,
                    'avg_dom': round(avg_dom) if avg_dom else 0
                })
        
        # Sort by count descending
        results.sort(key=lambda x: x['count'], reverse=True)
        return results
    
    # Helper methods
    def _median(self, values: List) -> float:
        """Calculate median"""
        if not values:
            return 0.0
        return statistics.median(values)
    
    def _average(self, values: List) -> float:
        """Calculate average"""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def _get_type_name(self, prop_type: str) -> str:
        """Get human-readable type name"""
        type_map = {
            'RES': 'Single Family Home',
            'CND': 'Condo',
            'MUL': 'Multi-Family',
            'LND': 'Land',
            'COM': 'Commercial'
        }
        return type_map.get(prop_type, prop_type)

# Usage
calculator = MarketCalculator(clean_properties)
snapshot = calculator.calculate_market_snapshot()

print(f"Market Snapshot for San Diego:")
print(f"  Active Listings: {snapshot['total_active']}")
print(f"  Median List Price: ${snapshot['median_list_price']:,}")
print(f"  Avg DOM: {snapshot['avg_dom']} days")
print(f"  Months of Inventory: {snapshot['months_of_inventory']}")
print(f"  Close/List Ratio: {snapshot['close_to_list_ratio']}%")
```

### 8.2 Trend Calculations

```python
from datetime import datetime, timedelta
from typing import List, Dict

class TrendCalculator:
    """
    Calculate trends and compare periods.
    """
    
    @staticmethod
    def calculate_period_comparison(current_properties: List[Dict], 
                                   previous_properties: List[Dict]) -> Dict:
        """
        Compare current period to previous period.
        
        Args:
            current_properties: Properties from current period
            previous_properties: Properties from previous period
        
        Returns:
            dict: Comparison metrics
        """
        current_calc = MarketCalculator(current_properties)
        previous_calc = MarketCalculator(previous_properties)
        
        current_stats = current_calc.calculate_market_snapshot()
        previous_stats = previous_calc.calculate_market_snapshot()
        
        def percent_change(current, previous):
            if previous == 0:
                return 0
            return round(((current - previous) / previous) * 100, 1)
        
        return {
            'active_listings': {
                'current': current_stats['total_active'],
                'previous': previous_stats['total_active'],
                'change': percent_change(current_stats['total_active'], previous_stats['total_active'])
            },
            'median_price': {
                'current': current_stats['median_list_price'],
                'previous': previous_stats['median_list_price'],
                'change': percent_change(current_stats['median_list_price'], previous_stats['median_list_price'])
            },
            'avg_dom': {
                'current': current_stats['avg_dom'],
                'previous': previous_stats['avg_dom'],
                'change': percent_change(current_stats['avg_dom'], previous_stats['avg_dom'])
            },
            'new_listings': {
                'current': current_stats['new_listings_7d'],
                'previous': previous_stats['new_listings_7d'],
                'change': percent_change(current_stats['new_listings_7d'], previous_stats['new_listings_7d'])
            }
        }
    
    @staticmethod
    def calculate_12_month_trend(monthly_data: List[Dict]) -> Dict:
        """
        Calculate 12-month trend from monthly data points.
        
        Args:
            monthly_data: List of monthly statistics
                [{'month': '2024-01', 'median_price': 950000}, ...]
        
        Returns:
            dict: Trend analysis
        """
        if len(monthly_data) < 2:
            return {'trend': 'insufficient_data'}
        
        # Sort by month
        sorted_data = sorted(monthly_data, key=lambda x: x['month'])
        
        # Calculate year-over-year change (12 months apart)
        if len(sorted_data) >= 12:
            yoy_change = percent_change(
                sorted_data[-1]['median_price'],
                sorted_data[-12]['median_price']
            )
        else:
            yoy_change = None
        
        # Calculate month-over-month change
        mom_change = percent_change(
            sorted_data[-1]['median_price'],
            sorted_data[-2]['median_price']
        )
        
        # Determine trend direction
        recent_months = sorted_data[-3:]
        prices = [m['median_price'] for m in recent_months]
        
        if prices[-1] > prices[0] * 1.02:
            trend = 'rising'
        elif prices[-1] < prices[0] * 0.98:
            trend = 'falling'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'yoy_change': yoy_change,
            'mom_change': mom_change,
            'current_price': sorted_data[-1]['median_price'],
            'data_points': len(sorted_data)
        }
```

---

## 9. Data Caching Strategy

### 9.1 Cache Architecture

```
API Response → Cache Check → Cache Hit? → Return Cached Data
                           → Cache Miss? → Fetch from API → Store in Cache → Return Data
```

### 9.2 Database Cache Implementation

**File**: `vcard-new/reports/core-system/cache.py`

```python
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import mysql.connector
from mysql.connector import Error

class ReportCache:
    """
    Database-backed cache for API responses and generated reports.
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                return True
        except Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def get_cached_report(self, employee_id: int, report_type: str, 
                         lookback_days: int) -> Optional[Dict]:
        """
        Retrieve cached report.
        
        Args:
            employee_id: Employee ID
            report_type: Type of report (e.g., 'market', 'inventory')
            lookback_days: Lookback period in days
        
        Returns:
            dict: Cached report data or None
        """
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor(dictionary=True)
        
        query = """
            SELECT * FROM market_report_cache
            WHERE employee_id = %s
              AND report_type = %s
              AND lookback_days = %s
              AND generated_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            ORDER BY generated_at DESC
            LIMIT 1
        """
        
        cursor.execute(query, (employee_id, report_type, lookback_days))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            # Load JSON data from file
            json_path = result['json_path']
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                
                return {
                    'data': data,
                    'html_path': result['html_path'],
                    'pdf_path': result['pdf_path'],
                    'generated_at': result['generated_at'],
                    'cache_key': result['cache_key']
                }
            except:
                return None
        
        return None
    
    def store_report(self, employee_id: int, report_type: str, lookback_days: int,
                    report_data: Dict, html_path: str, pdf_path: str = None) -> bool:
        """
        Store report in cache.
        
        Args:
            employee_id: Employee ID
            report_type: Type of report
            lookback_days: Lookback period
            report_data: Report data (will be saved as JSON)
            html_path: Path to HTML report file
            pdf_path: Path to PDF file (optional)
        
        Returns:
            bool: Success status
        """
        if not self.connection:
            self.connect()
        
        # Generate cache key
        cache_key = self._generate_cache_key(employee_id, report_type, lookback_days)
        
        # Save JSON data to file
        json_path = f"cache/reports/{cache_key}.json"
        try:
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2)
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return False
        
        # Store in database
        cursor = self.connection.cursor()
        
        query = """
            INSERT INTO market_report_cache
            (employee_id, report_type, lookback_days, json_path, html_path, 
             pdf_path, generated_at, cache_key)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
        """
        
        try:
            cursor.execute(query, (
                employee_id, report_type, lookback_days,
                json_path, html_path, pdf_path, cache_key
            ))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Database insert error: {e}")
            cursor.close()
            return False
    
    def invalidate_cache(self, employee_id: int = None, report_type: str = None):
        """
        Invalidate cache entries.
        
        Args:
            employee_id: Specific employee (optional)
            report_type: Specific report type (optional)
        """
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        if employee_id and report_type:
            query = "DELETE FROM market_report_cache WHERE employee_id = %s AND report_type = %s"
            cursor.execute(query, (employee_id, report_type))
        elif employee_id:
            query = "DELETE FROM market_report_cache WHERE employee_id = %s"
            cursor.execute(query, (employee_id,))
        elif report_type:
            query = "DELETE FROM market_report_cache WHERE report_type = %s"
            cursor.execute(query, (report_type,))
        else:
            # Clear all old cache (older than 24 hours)
            query = "DELETE FROM market_report_cache WHERE generated_at < DATE_SUB(NOW(), INTERVAL 24 HOUR)"
            cursor.execute(query)
        
        self.connection.commit()
        cursor.close()
    
    def _generate_cache_key(self, employee_id: int, report_type: str, lookback_days: int) -> str:
        """Generate unique cache key"""
        data = f"{employee_id}:{report_type}:{lookback_days}:{datetime.now().strftime('%Y-%m-%d-%H')}"
        return hashlib.md5(data.encode()).hexdigest()

# Usage
cache = ReportCache({
    'host': 'localhost',
    'database': 'pct_reports',
    'user': 'reports_user',
    'password': 'secure_password'
})

# Try to get cached report
cached = cache.get_cached_report(employee_id=123, report_type='market', lookback_days=30)

if cached:
    print(f"Using cached report from {cached['generated_at']}")
    report_data = cached['data']
else:
    print("Cache miss. Generating new report...")
    # Fetch from API and generate report
    report_data = generate_new_report()
    
    # Store in cache
    cache.store_report(
        employee_id=123,
        report_type='market',
        lookback_days=30,
        report_data=report_data,
        html_path='reports/market_123.html'
    )

cache.close()
```

---

## Part 3: Report Generation System

---

## 10. Report Architecture Overview

### 10.1 Report Generation Flow

```
1. User Request → Report API
2. Check Cache → Cache Hit? Return Cached HTML
3. Cache Miss → Fetch Data from SimplyRETS
4. Process & Calculate Metrics
5. Generate HTML from Template
6. Store in Cache
7. Return HTML to User
```

### 10.2 Template System

Each report uses an HTML template with placeholders that get replaced with actual data.

**Template Placeholders**:
```html
{{market_name}}       → San Diego
{{period_label}}      → Last 30 days
{{median_price}}      → $975,000
{{closed_sales}}      → 205
{{avg_dom}}           → 27
```

### 10.3 Report File Structure

```
vcard-new/
  ├── pct-market-snapshot.html         # Market Snapshot template
  ├── pct-new-listings-by-city.html    # New Listings template
  ├── pct-inventory-by-city.html       # Inventory template
  ├── pct-closed-by-city.html          # Closed Listings template
  ├── pct-price-bands.html             # Price Bands template
  ├── pct-open-houses-by-city.html     # Open Houses template
```

---

## 11. Market Snapshot Report

### 11.1 Purpose & Use Case

**Market Snapshot** provides a comprehensive overview of market activity in a specific city over the past N days (typically 30).

**Key Metrics**:
- Median Sale Price
- Closed Sales Count
- Average Days on Market (DOM)
- Months of Inventory (MOI)
- New Listings
- Pending Sales
- Sale-to-List Ratio

**Use Cases**:
- Monthly market updates for clients
- Market condition assessment
- Lead generation (social media posts)
- Client presentations

### 11.2 Data Requirements

**API Calls Needed**:
1. Get all listings for city (Active, Pending, Closed) for past 30 days
2. Optional: Get previous 30 days for comparison

**Minimum Data Points**: 10 closed sales for reliable median

### 11.3 HTML Structure

**File**: `vcard-new/pct-market-snapshot.html`

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>PCT • Market Snapshot</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    /* Print-optimized styling */
    @page {
      size: letter;
      margin: 0.2in;
    }
    
    /* Color scheme */
    :root {
      --pct-blue: rgb(37,99,235);
      --pct-accent: #f26b2b;
      --ink: #0f172a;
      --muted: #6b7280;
      --border: #e5e7eb;
    }
    
    /* Layout */
    .page {
      width: 8.5in;
      min-height: 11in;
      margin: 0 auto;
      background: white;
      padding: 0.25in;
    }
    
    /* Header */
    .header {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 16px;
      align-items: center;
    }
    
    /* Hero Ribbon */
    .ribbon {
      background: linear-gradient(90deg, var(--pct-blue), var(--pct-accent));
      color: #fff;
      border-radius: 14px;
      padding: 14px 18px;
      margin: 6px 0 16px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
    }
    
    /* Stats Grid */
    .stat-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }
    
    /* More styling... */
  </style>
</head>
<body>
  <!-- Action Buttons (screen only) -->
  <div class="action-buttons no-print">
    <button class="print-btn" onclick="window.print()">🖨️ Print / Save PDF</button>
    <button class="social-btn" onclick="openSocialModal()">📱 Generate Social Graphic</button>
  </div>

  <!-- Main Content -->
  <div class="page">
    <!-- Header -->
    <header class="header">
      <div class="brand">
        <img src="https://pct.com/vcard-new/assets/images/logo2-dark.png" alt="Pacific Coast Title" />
        <div class="title-block">
          <h1>Market Snapshot — {{market_name}}</h1>
          <div class="sub">Period: {{period_label}} • Source: CRMLS/MLS • Report Date: {{report_date}}</div>
        </div>
      </div>
      <div class="badge">PCT Insights</div>
    </header>

    <!-- Hero Ribbon with Key Metrics -->
    <section class="ribbon">
      <div class="kpi">
        <div class="item">
          <div class="lbl">Median Sale Price</div>
          <div class="val">{{median_price}}</div>
        </div>
        <div class="item">
          <div class="lbl">Closed Sales</div>
          <div class="val">{{closed_sales}}</div>
        </div>
        <div class="item">
          <div class="lbl">Avg. Days on Market</div>
          <div class="val">{{avg_dom}}</div>
        </div>
        <div class="item">
          <div class="lbl">Months of Inventory</div>
          <div class="val">{{moi}}</div>
        </div>
      </div>
      <div class="chip">Last {{lookback_days}} days</div>
    </section>

    <!-- Core Indicators Card -->
    <div class="card">
      <h3>Core Indicators</h3>
      <div class="stat-grid">
        <div class="mini">
          <div class="label">New Listings</div>
          <div class="value">{{new_listings}}</div>
          <div class="delta {{new_listings_delta_class}}">
            {{new_listings_delta}}%
          </div>
        </div>
        <div class="mini">
          <div class="label">Pending Sales</div>
          <div class="value">{{pendings}}</div>
          <div class="delta {{pendings_delta_class}}">
            {{pendings_delta}}%
          </div>
        </div>
        <div class="mini">
          <div class="label">Sale-to-List Ratio</div>
          <div class="value">{{close_to_list_ratio}}%</div>
        </div>
      </div>
    </div>

    <!-- 12-Month Trend (SVG Sparkline) -->
    <div class="card">
      <h3>12-Month Trend (Median Price)</h3>
      <svg class="spark" viewBox="0 0 300 60" preserveAspectRatio="none">
        <path d="{{trend_path_data}}" />
      </svg>
      <div class="trend-stats">
        Latest: <strong>{{median_price}}</strong> • YoY: <strong>{{median_price_yoy}}%</strong>
      </div>
    </div>

    <!-- Property Type Breakdown -->
    <div class="grid-2">
      <div class="card">
        <h3>By Property Type</h3>
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th class="t-right">Median Price</th>
              <th class="t-right">Closed</th>
              <th class="t-right">DOM</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>SFR</td><td class="t-right">{{sfr_median}}</td><td class="t-right">{{sfr_closed}}</td><td class="t-right">{{sfr_dom}}</td></tr>
            <tr><td>Condo</td><td class="t-right">{{condo_median}}</td><td class="t-right">{{condo_closed}}</td><td class="t-right">{{condo_dom}}</td></tr>
            <tr><td>Townhome</td><td class="t-right">{{th_median}}</td><td class="t-right">{{th_closed}}</td><td class="t-right">{{th_dom}}</td></tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <h3>By Price Tier</h3>
        <table>
          <thead>
            <tr>
              <th>Tier</th>
              <th class="t-right">Median</th>
              <th class="t-right">Closed</th>
              <th class="t-right">MOI</th>
            </tr>
          </thead>
          <tbody>
            <tr><td><span class="chip">Entry</span></td><td class="t-right">{{tier1_median}}</td><td class="t-right">{{tier1_closed}}</td><td class="t-right">{{tier1_moi}}</td></tr>
            <tr><td><span class="chip">Move-Up</span></td><td class="t-right">{{tier2_median}}</td><td class="t-right">{{tier2_closed}}</td><td class="t-right">{{tier2_moi}}</td></tr>
            <tr><td><span class="chip">Luxury</span></td><td class="t-right">{{tier3_median}}</td><td class="t-right">{{tier3_closed}}</td><td class="t-right">{{tier3_moi}}</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Footer -->
    <footer class="footer">
      <div class="foot-notes">
        Notes: Residential resale only. Data reflect {{period_label}} activity and may be revised by MLS.
      </div>
      <div class="brandbar">
        <span class="tag">Pacific Coast Title • Market Intelligence</span>
      </div>
    </footer>
  </div>

  <!-- JavaScript for Social Modal -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
  <script>
    // window.DATA will be populated by Python
    window.DATA = {{DATA_JSON}};
    window.EMPLOYEE_DATA = {{EMPLOYEE_JSON}};
    
    // Social modal functions...
    function extractReportData() {
      return {
        city_name: document.querySelector('.title-block h1')?.textContent.replace('Market Snapshot — ', '').trim(),
        median_price: window.DATA?.median_price || 0,
        closed_sales: window.DATA?.counts?.Closed || 0,
        active_listings: window.DATA?.counts?.Active || 0,
        avg_dom: window.DATA?.avg_dom || 0,
        rep_name: window.EMPLOYEE_DATA?.name || '',
        rep_title: window.EMPLOYEE_DATA?.title || '',
        rep_contact: window.EMPLOYEE_DATA?.email || '',
        rep_photo: window.EMPLOYEE_DATA?.photo || ''
      };
    }
    
    function buildSocialURL(theme = '') {
      const data = extractReportData();
      const baseURL = '/vcard-new/socialtemplates-v4/index.html';
      
      const params = new URLSearchParams({
        city_name: data.city_name,
        period_label: 'Market Snapshot',
        median_price: data.median_price,
        closed_sales: data.closed_sales,
        active_listings: data.active_listings,
        avg_dom: Math.round(data.avg_dom),
        rep_name: data.rep_name,
        rep_title: data.rep_title,
        rep_contact: data.rep_contact,
        rep_photo: data.rep_photo,
        theme: theme
      });
      
      return `${baseURL}?${params.toString()}`;
    }
    
    function openSocialModal() {
      document.getElementById('socialModal').classList.add('active');
      updatePreview();
    }
    
    function closeSocialModal() {
      document.getElementById('socialModal').classList.remove('active');
    }
    
    function updatePreview() {
      const theme = document.getElementById('themeSelect').value;
      const iframe = document.getElementById('socialPreview');
      iframe.src = buildSocialURL(theme);
    }
    
    async function downloadSocialGraphic() {
      // html2canvas export logic (covered in Section 24)
    }
  </script>
</body>
</html>
```

### 11.4 Python Report Generator

**File**: `vcard-new/reports/core-system/market_snapshot_generator.py`

```python
from datetime import datetime, timedelta
from typing import Dict
import json

class MarketSnapshotGenerator:
    """
    Generate Market Snapshot reports.
    """
    
    def __init__(self, api_client, calculator, template_path):
        self.api_client = api_client
        self.calculator = calculator
        self.template_path = template_path
    
    def generate_report(self, city: str, lookback_days: int = 30, 
                       employee_data: Dict = None) -> str:
        """
        Generate a complete Market Snapshot report.
        
        Args:
            city: City name
            lookback_days: Days to look back
            employee_data: Employee/rep information
        
        Returns:
            str: Generated HTML report
        """
        # 1. Fetch data from API
        print(f"Fetching data for {city} (last {lookback_days} days)...")
        properties = self.api_client.get_market_snapshot_data(city, lookback_days)
        
        # 2. Validate & clean data
        validator = PropertyValidator()
        validation_results = validator.validate_batch(properties)
        clean_properties = validation_results['valid']
        
        print(f"Fetched {len(properties)} properties, {len(clean_properties)} valid")
        
        # 3. Calculate metrics
        calc = MarketCalculator(clean_properties)
        metrics = calc.calculate_market_snapshot()
        by_type = calc.calculate_by_property_type()
        
        # 4. Calculate price tiers
        price_bands = [
            {'name': 'Entry', 'min': 0, 'max': 500000},
            {'name': 'Move-Up', 'min': 500000, 'max': 1500000},
            {'name': 'Luxury', 'min': 1500000, 'max': 999999999}
        ]
        tier_stats = calc.calculate_price_bands(price_bands)
        
        # 5. Format data for template
        template_data = {
            # Header
            'market_name': city,
            'period_label': f"Last {lookback_days} days",
            'report_date': datetime.now().strftime('%B %d, %Y'),
            'lookback_days': lookback_days,
            
            # Hero metrics
            'median_price': self._format_price(metrics['median_close_price']),
            'closed_sales': metrics['total_closed'],
            'avg_dom': metrics['avg_dom'],
            'moi': metrics['months_of_inventory'],
            
            # Core indicators
            'new_listings': metrics['new_listings_7d'],
            'new_listings_delta': '+5.2',  # Would calculate from comparison
            'new_listings_delta_class': 'up',
            'pendings': metrics['total_pending'],
            'pendings_delta': '+2.1',
            'pendings_delta_class': 'up',
            'close_to_list_ratio': metrics['close_to_list_ratio'],
            
            # Trend data
            'trend_path_data': 'M0,42 L27,38 L54,36...',  # Would generate from historical data
            'median_price_yoy': '+8.5',
            'median_price_mom': '+1.2',
            
            # By property type
            'sfr_median': self._format_price(by_type[0]['median_price']) if by_type else '$0',
            'sfr_closed': by_type[0]['count'] if by_type else 0,
            'sfr_dom': by_type[0]['avg_dom'] if by_type else 0,
            # ... more types
            
            # By price tier
            'tier1_median': self._format_price(tier_stats[0]['medianPrice']) if tier_stats else '$0',
            'tier1_closed': tier_stats[0]['count'] if tier_stats else 0,
            'tier1_moi': '2.5',  # Would calculate per tier
            # ... more tiers
            
            # Data for JavaScript
            'DATA_JSON': json.dumps(metrics),
            'EMPLOYEE_JSON': json.dumps(employee_data or {})
        }
        
        # 6. Load template and replace placeholders
        html = self._load_template()
        html = self._replace_placeholders(html, template_data)
        
        return html
    
    def _load_template(self) -> str:
        """Load HTML template"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _replace_placeholders(self, html: str, data: Dict) -> str:
        """Replace {{placeholders}} with actual data"""
        for key, value in data.items():
            placeholder = '{{' + key + '}}'
            html = html.replace(placeholder, str(value))
        return html
    
    def _format_price(self, price: int) -> str:
        """Format price as currency"""
        if not price:
            return '$0'
        return f"${price:,}"

# Usage
generator = MarketSnapshotGenerator(
    api_client=simplyrets_client,
    calculator=MarketCalculator,
    template_path='vcard-new/pct-market-snapshot.html'
)

employee_data = {
    'name': 'Jorge Mesa',
    'title': 'Title Rep • Pacific Coast Title',
    'email': 'jmesa@pct.com',
    'phone': '(714) 555-1212',
    'photo': 'https://pct.com/photos/jorge.jpg'
}

html_report = generator.generate_report(
    city='San Diego',
    lookback_days=30,
    employee_data=employee_data
)

# Save report
output_path = f"reports/market-snapshot-san-diego-{datetime.now().strftime('%Y%m%d')}.html"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_report)

print(f"Report saved to: {output_path}")
```

---

*Due to the massive scope of this documentation, I'm providing this in sections. This document continues with the remaining report types, social graphics system, PDF generation, database schema, and deployment procedures.*

**Would you like me to continue generating the remaining sections (12-32)?** This will be an extremely comprehensive reference document covering every detail you requested.

The documentation so far covers:
✅ Part 1: Complete API Integration (Sections 1-6)
✅ Part 2: Data Processing Pipeline (Sections 7-9)  
✅ Part 3: Report Generation (Sections 10-11 started)

**Remaining**: Sections 12-32 covering all other reports, social graphics (5 templates), themes, html2canvas, PDF, database, deployment, and troubleshooting.

