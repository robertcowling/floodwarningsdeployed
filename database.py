from replit import db
from datetime import datetime
import json

def store_counts(timestamp, data):
    """Store flood counts in the database"""
    db[timestamp] = json.dumps(data)

def get_latest_counts():
    """Get the most recent flood counts"""
    if not db.keys():
        return None
    
    latest_key = max(db.keys())
    return json.loads(db[latest_key])

def get_counts_between_dates(start_date, end_date):
    """Get flood counts between two dates"""
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()
    
    results = []
    for key in db.keys():
        if start_str <= key <= end_str:
            data = json.loads(db[key])
            results.append(data)
    
    return sorted(results, key=lambda x: x['timestamp'])
