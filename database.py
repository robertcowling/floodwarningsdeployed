from datetime import datetime, timedelta
from collections import OrderedDict
from storage import GCSStorage
from statistics import mean
import traceback

# Initialize GCS storage
storage = GCSStorage()

def _normalize_timestamp(timestamp):
    """Normalize timestamp to nearest 15-minute interval"""
    try:
        dt = datetime.fromisoformat(timestamp)
        minutes = dt.minute
        normalized_minutes = (minutes // 15) * 15
        normalized_dt = dt.replace(minute=normalized_minutes, second=0, microsecond=0)
        print(f"Normalized timestamp: {timestamp} -> {normalized_dt.isoformat()}")
        return normalized_dt.isoformat()
    except Exception as e:
        print(f"Error normalizing timestamp: {e}")
        print("Stack trace:", traceback.format_exc())
        raise

def _create_ordered_response(data):
    """Create consistently ordered response dictionary"""
    try:
        ordered_data = OrderedDict([
            ('timestamp', data.get('timestamp')),
            ('severes', data.get('severes', 0)),
            ('warnings', data.get('warnings', 0)),
            ('alerts', data.get('alerts', 0))
        ])
        print(f"Created ordered response: {ordered_data}")
        return ordered_data
    except Exception as e:
        print(f"Error creating ordered response: {e}")
        print("Stack trace:", traceback.format_exc())
        raise

def _aggregate_data(data_points, interval_hours=1):
    """Aggregate data points by averaging values over specified interval"""
    if not data_points:
        print("No data points to aggregate")
        return []
    
    try:
        # Sort data points by timestamp
        sorted_data = sorted(data_points, key=lambda x: x['timestamp'])
        print(f"Aggregating {len(sorted_data)} data points with {interval_hours}h interval")
        
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
        
        print(f"Aggregated to {len(aggregated_data)} data points")
        return aggregated_data
        
    except Exception as e:
        print(f"Error aggregating data: {e}")
        print("Stack trace:", traceback.format_exc())
        return []

def store_counts(timestamp, data):
    """Store flood counts in the database with timestamp validation"""
    try:
        print(f"Storing counts for timestamp: {timestamp}")
        print(f"Input data: {data}")
        
        # Normalize the timestamp to nearest 15-minute interval
        normalized_timestamp = _normalize_timestamp(timestamp)
        
        # Update the timestamp in the data
        ordered_data = _create_ordered_response({
            'timestamp': normalized_timestamp,
            'severes': data.get('severes', 0),
            'warnings': data.get('warnings', 0),
            'alerts': data.get('alerts', 0)
        })
        
        # Store the data with normalized timestamp
        storage.store_counts(normalized_timestamp, ordered_data)
        print(f"Successfully stored counts with normalized timestamp: {normalized_timestamp}")
        
    except Exception as e:
        print(f"Error storing counts: {e}")
        print("Stack trace:", traceback.format_exc())
        raise

def get_latest_counts():
    """Get the most recent flood counts"""
    try:
        print("Fetching latest flood counts")
        data = storage.get_latest_counts()
        
        if not data:
            print("No data found, creating default response")
            return _create_ordered_response({
                'timestamp': datetime.now().isoformat()
            })
        
        print(f"Retrieved latest counts: {data}")
        return _create_ordered_response(data)
    except Exception as e:
        print(f"Error getting latest counts: {e}")
        print("Stack trace:", traceback.format_exc())
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
        
        if not results:
            print("No results found for the date range")
            return [_create_ordered_response({
                'timestamp': datetime.now().isoformat()
            })]
        
        # Calculate time difference
        time_diff = end_date - start_date
        print(f"Time difference: {time_diff}")
        
        # Apply aggregation based on time range
        if time_diff > timedelta(days=7):
            print("Applying 6-hour aggregation for period > 7 days")
            results = _aggregate_data(results, interval_hours=6)
        elif time_diff > timedelta(days=2):
            print("Applying 2-hour aggregation for period > 2 days")
            results = _aggregate_data(results, interval_hours=2)
        elif time_diff > timedelta(days=1):
            print("Applying 1-hour aggregation for period > 1 day")
            results = _aggregate_data(results, interval_hours=1)
        
        sorted_results = sorted(results, key=lambda x: x['timestamp'])
        print(f"Returning {len(sorted_results)} records")
        
        return sorted_results
    except Exception as e:
        print(f"Error getting counts between dates: {e}")
        print("Stack trace:", traceback.format_exc())
        return [_create_ordered_response({
            'timestamp': datetime.now().isoformat()
        })]
