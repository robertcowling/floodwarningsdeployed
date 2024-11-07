import requests
from datetime import datetime
import database
import json

FLOOD_API_URL = "http://environment.data.gov.uk/flood-monitoring/id/floods"

def fetch_flood_data():
    """Fetch flood data from the Environment Agency API"""
    try:
        print(f"Fetching flood data from {FLOOD_API_URL}")
        response = requests.get(FLOOD_API_URL)
        response.raise_for_status()
        data = response.json()
        print(f"Successfully fetched flood data with {len(data.get('items', []))} items")
        return data
    except requests.RequestException as e:
        print(f"Error fetching flood data: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

def count_severity_levels(flood_data):
    """Count the number of alerts, warnings, and severe warnings"""
    if not flood_data or 'items' not in flood_data:
        print("Warning: No flood data or items available")
        return {'alerts': 0, 'warnings': 0, 'severes': 0}
    
    counts = {
        'alerts': 0,    # severity level 3
        'warnings': 0,  # severity level 2
        'severes': 0    # severity level 1
    }
    
    try:
        for item in flood_data['items']:
            severity_level = item.get('severityLevel')
            if severity_level == 3:
                counts['alerts'] += 1
            elif severity_level == 2:
                counts['warnings'] += 1
            elif severity_level == 1:
                counts['severes'] += 1
        
        print(f"Counted severity levels: {counts}")
        return counts
    except Exception as e:
        print(f"Error counting severity levels: {e}")
        return {'alerts': 0, 'warnings': 0, 'severes': 0}

def fetch_and_store_flood_data():
    """Fetch flood data and store counts in the database"""
    try:
        print("Starting flood data fetch and store process")
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
            print(f"Successfully stored flood data: {data}")
        else:
            print("No flood data available to store")
    except Exception as e:
        print(f"Error in fetch_and_store_flood_data: {e}")
