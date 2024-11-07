from replit import db
from datetime import datetime, timedelta
import json

def _normalize_timestamp(timestamp):
    """Normalize timestamp to nearest 15-minute interval"""
    dt = datetime.fromisoformat(timestamp)
    minutes = dt.minute
    normalized_minutes = (minutes // 15) * 15
    return dt.replace(minute=normalized_minutes, second=0, microsecond=0).isoformat()

def _cleanup_intermediate_timestamps():
    """Clean up timestamps that don't align with 15-minute intervals"""
    keys_to_remove = []
    for key in db.keys():
        try:
            timestamp = datetime.fromisoformat(key)
            if timestamp.minute % 15 != 0 or timestamp.second != 0:
                keys_to_remove.append(key)
        except (ValueError, TypeError):
            continue
    
    for key in keys_to_remove:
        del db[key]

def store_counts(timestamp, data):
    """Store flood counts in the database with timestamp validation"""
    try:
        # Normalize the timestamp to nearest 15-minute interval
        normalized_timestamp = _normalize_timestamp(timestamp)
        print(f"Normalizing timestamp from {timestamp} to {normalized_timestamp}")
        
        # Update the timestamp in the data
        data['timestamp'] = normalized_timestamp
        
        # Store the data with normalized timestamp
        db[normalized_timestamp] = json.dumps(data)
        print(f"Successfully stored counts in database at {normalized_timestamp}")
        
        # Periodically clean up intermediate timestamps
        _cleanup_intermediate_timestamps()
    except Exception as e:
        print(f"Error storing counts in database: {e}")

def get_latest_counts():
    """Get the most recent flood counts"""
    try:
        keys = list(db.keys())
        if not keys:
            print("No data found in database")
            return {'alerts': 0, 'warnings': 0, 'severes': 0, 'timestamp': datetime.now().isoformat()}
        
        latest_key = max(keys)
        data = json.loads(db[latest_key])
        print(f"Retrieved latest counts: {data}")
        return data
    except Exception as e:
        print(f"Error getting latest counts: {e}")
        return {'alerts': 0, 'warnings': 0, 'severes': 0, 'timestamp': datetime.now().isoformat()}

def get_counts_between_dates(start_date, end_date):
    """Get flood counts between two dates"""
    try:
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        
        print(f"Fetching counts between {start_str} and {end_str}")
        results = []
        for key in db.keys():
            if start_str <= key <= end_str:
                data = json.loads(db[key])
                results.append(data)
        
        sorted_results = sorted(results, key=lambda x: x['timestamp'])
        print(f"Found {len(sorted_results)} records")
        
        # Return at least one data point if no data is found
        if not sorted_results:
            return [{'alerts': 0, 'warnings': 0, 'severes': 0, 'timestamp': datetime.now().isoformat()}]
        
        return sorted_results
    except Exception as e:
        print(f"Error getting counts between dates: {e}")
        return [{'alerts': 0, 'warnings': 0, 'severes': 0, 'timestamp': datetime.now().isoformat()}]
