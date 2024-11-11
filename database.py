from datetime import datetime, timedelta
from collections import OrderedDict
from storage import GCSStorage
from statistics import mean

# Initialize GCS storage
storage = GCSStorage()

def _normalize_timestamp(timestamp):
    """Normalize timestamp to nearest 15-minute interval"""
    dt = datetime.fromisoformat(timestamp)
    minutes = dt.minute
    normalized_minutes = (minutes // 15) * 15
    return dt.replace(minute=normalized_minutes, second=0, microsecond=0).isoformat()

def _create_ordered_response(data):
    """Create consistently ordered response dictionary"""
    return OrderedDict([
        ('timestamp', data.get('timestamp')),
        ('severes', data.get('severes', 0)),
        ('warnings', data.get('warnings', 0)),
        ('alerts', data.get('alerts', 0))
    ])

def _aggregate_data(data_points, interval_hours=1):
    """Aggregate data points by averaging values over specified interval"""
    if not data_points:
        return []
    
    # Sort data points by timestamp
    sorted_data = sorted(data_points, key=lambda x: x['timestamp'])
    aggregated_data = []
    current_group = []
    interval = timedelta(hours=interval_hours)
    
    # Get the first timestamp as reference
    current_interval_start = datetime.fromisoformat(sorted_data[0]['timestamp'])
    
    for point in sorted_data:
        timestamp = datetime.fromisoformat(point['timestamp'])
        if timestamp < current_interval_start + interval:
            current_group.append(point)
        else:
            if current_group:
                # Calculate averages for the current group
                avg_data = {
                    'timestamp': current_interval_start.isoformat(),
                    'severes': round(mean(d['severes'] for d in current_group)),
                    'warnings': round(mean(d['warnings'] for d in current_group)),
                    'alerts': round(mean(d['alerts'] for d in current_group))
                }
                aggregated_data.append(_create_ordered_response(avg_data))
            
            # Start new group
            current_interval_start = timestamp
            current_group = [point]
    
    # Handle the last group
    if current_group:
        avg_data = {
            'timestamp': current_interval_start.isoformat(),
            'severes': round(mean(d['severes'] for d in current_group)),
            'warnings': round(mean(d['warnings'] for d in current_group)),
            'alerts': round(mean(d['alerts'] for d in current_group))
        }
        aggregated_data.append(_create_ordered_response(avg_data))
    
    return aggregated_data

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
        
        # Store the data with normalized timestamp
        storage.store_counts(normalized_timestamp, ordered_data)
        print(f"Successfully stored counts in GCS at {normalized_timestamp}")
        
    except Exception as e:
        print(f"Error storing counts in GCS: {e}")

def get_latest_counts():
    """Get the most recent flood counts"""
    try:
        data = storage.get_latest_counts()
        if not data:
            print("No data found in storage")
            return _create_ordered_response({
                'timestamp': datetime.now().isoformat()
            })
        
        print(f"Retrieved latest counts: {data}")
        return _create_ordered_response(data)
    except Exception as e:
        print(f"Error getting latest counts: {e}")
        return _create_ordered_response({
            'timestamp': datetime.now().isoformat()
        })

def get_counts_between_dates(start_date, end_date):
    """Get flood counts between two dates with automatic aggregation for longer periods"""
    try:
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        
        print(f"Fetching counts between {start_str} and {end_str}")
        results = storage.get_counts_between_dates(start_date, end_date)
        
        # Calculate time difference
        time_diff = end_date - start_date
        
        # Apply aggregation based on time range
        if time_diff > timedelta(days=7):
            # For periods > 7 days, aggregate by 6 hours
            results = _aggregate_data(results, interval_hours=6)
        elif time_diff > timedelta(days=2):
            # For periods > 2 days, aggregate by 2 hours
            results = _aggregate_data(results, interval_hours=2)
        elif time_diff > timedelta(days=1):
            # For periods > 1 day, aggregate by 1 hour
            results = _aggregate_data(results, interval_hours=1)
        
        sorted_results = sorted(results, key=lambda x: x['timestamp'])
        print(f"Found {len(sorted_results)} records")
        
        # Return at least one data point if no data is found
        if not sorted_results:
            return [_create_ordered_response({
                'timestamp': datetime.now().isoformat()
            })]
        
        return sorted_results
    except Exception as e:
        print(f"Error getting counts between dates: {e}")
        return [_create_ordered_response({
            'timestamp': datetime.now().isoformat()
        })]