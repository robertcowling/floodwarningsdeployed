import requests
from datetime import datetime
import database

FLOOD_API_URL = "http://environment.data.gov.uk/flood-monitoring/id/floods"

def fetch_flood_data():
    """Fetch flood data from the Environment Agency API"""
    try:
        response = requests.get(FLOOD_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching flood data: {e}")
        return None

def count_severity_levels(flood_data):
    """Count the number of alerts, warnings, and severe warnings"""
    if not flood_data or 'items' not in flood_data:
        return {'alerts': 0, 'warnings': 0, 'severes': 0}
    
    counts = {
        'alerts': 0,    # severity level 3
        'warnings': 0,  # severity level 2
        'severes': 0    # severity level 1
    }
    
    for item in flood_data['items']:
        severity_level = item.get('severityLevel')
        if severity_level == 3:
            counts['alerts'] += 1
        elif severity_level == 2:
            counts['warnings'] += 1
        elif severity_level == 1:
            counts['severes'] += 1
    
    return counts

def fetch_and_store_flood_data():
    """Fetch flood data and store counts in the database"""
    flood_data = fetch_flood_data()
    if flood_data:
        counts = count_severity_levels(flood_data)
        timestamp = datetime.now().isoformat()
        
        data = {
            'timestamp': timestamp,
            'alerts': counts['alerts'],
            'warnings': counts['warnings'],
            'severes': counts['severes']
        }
        
        database.store_counts(timestamp, data)
