from replit import db
from datetime import datetime, timedelta
import json
from collections import OrderedDict
import zlib

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

class OrderedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, OrderedDict):
            return dict(obj)
        return super().default(obj)

def _create_ordered_response(data):
    """Create consistently ordered response dictionary"""
    return OrderedDict([
        ('timestamp', data.get('timestamp')),
        ('severes', data.get('severes', 0)),
        ('warnings', data.get('warnings', 0)),
        ('alerts', data.get('alerts', 0))
    ])

def store_counts(timestamp, data):
    """Store flood counts in the database with timestamp validation"""
    try:
        # Normalize the timestamp to nearest 15-minute interval
        normalized_timestamp = _normalize_timestamp(timestamp)
        print(f"Normalizing timestamp from {timestamp} to {normalized_timestamp}")
        
        # Update the timestamp in the data
        ordered_data = _create_ordered_response({
            'timestamp': normalized_timestamp,
            'severes': data.get('severes', 0),
            'warnings': data.get('warnings', 0),
            'alerts': data.get('alerts', 0)
        })
        
        # Store the data with normalized timestamp using custom encoder
        db[normalized_timestamp] = json.dumps(ordered_data, cls=OrderedJSONEncoder, sort_keys=False)
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
            return _create_ordered_response({
                'timestamp': datetime.now().isoformat()
            })
        
        latest_key = max(keys)
        data = json.loads(db[latest_key])
        print(f"Retrieved latest counts: {data}")
        return _create_ordered_response(data)
    except Exception as e:
        print(f"Error getting latest counts: {e}")
        return _create_ordered_response({
            'timestamp': datetime.now().isoformat()
        })

def get_counts_between_dates(start_date, end_date, page=1, per_page=100):
    """Get flood counts between two dates with pagination"""
    try:
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        
        print(f"Fetching counts between {start_str} and {end_str}")
        results = []
        for key in db.keys():
            if start_str <= key <= end_str:
                data = json.loads(db[key])
                results.append(_create_ordered_response(data))
        
        # Sort results
        sorted_results = sorted(results, key=lambda x: x['timestamp'])
        
        # Implement pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = sorted_results[start_idx:end_idx]
        
        # Return at least one data point if no data is found
        if not paginated_results:
            return [_create_ordered_response({
                'timestamp': datetime.now().isoformat()
            })]
        
        return paginated_results
    except Exception as e:
        print(f"Error getting counts between dates: {e}")
        return [_create_ordered_response({
            'timestamp': datetime.now().isoformat()
        })]