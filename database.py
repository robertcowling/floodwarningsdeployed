from replit import db
from datetime import datetime
import json

def store_counts(timestamp, data):
    """Store flood counts in the database"""
    try:
        print(f"Storing counts for timestamp: {timestamp}")
        db[timestamp] = json.dumps(data)
        print("Successfully stored counts in database")
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
