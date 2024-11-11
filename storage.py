from google.cloud import storage
from google.oauth2 import service_account
import json
import csv
from datetime import datetime, timedelta
import io
from collections import OrderedDict
import os
import base64
import traceback

class GCSStorage:
    def __init__(self):
        try:
            # Load credentials from environment variable
            credentials_json = os.environ.get('GOOGLE_CLOUD_CREDENTIALS')
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
            
            if not credentials_json or not project_id:
                raise EnvironmentError("Missing required Google Cloud credentials")
            
            print("Attempting to initialize Google Cloud Storage...")
            
            # Try to decode and parse credentials in multiple formats
            credentials_info = None
            error_messages = []
            
            # Try method 1: Direct JSON parsing
            try:
                credentials_info = json.loads(credentials_json)
                print("Successfully parsed credentials as direct JSON")
            except json.JSONDecodeError as e:
                error_messages.append(f"Direct JSON parsing failed: {e}")
                
                # Try method 2: Base64 decoding
                try:
                    decoded = base64.b64decode(credentials_json).decode('utf-8')
                    credentials_info = json.loads(decoded)
                    print("Successfully parsed credentials from base64")
                except Exception as e:
                    error_messages.append(f"Base64 decoding failed: {e}")
            
            if not credentials_info:
                raise Exception(f"Failed to parse credentials: {'; '.join(error_messages)}")
            
            # Verify required fields in credentials
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key']
            missing_fields = [field for field in required_fields if field not in credentials_info]
            if missing_fields:
                raise Exception(f"Credentials missing required fields: {', '.join(missing_fields)}")
            
            self.bucket_name = f"{project_id}-flood-data"
            print(f"Using bucket: {self.bucket_name}")
            
            # Initialize client with explicit credentials
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info
            )
            
            self.client = storage.Client(
                project=project_id,
                credentials=credentials
            )
            
            # Ensure bucket exists
            self.ensure_bucket_exists()
            print("Successfully initialized Google Cloud Storage")
            
            # Create cache directory for local development
            os.makedirs('data_cache', exist_ok=True)
            
        except Exception as e:
            print(f"Error initializing Google Cloud Storage: {e}")
            print("Falling back to local file storage")
            self.use_local_storage = True
            os.makedirs('data_cache', exist_ok=True)
    
    def ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't"""
        try:
            self.bucket = self.client.get_bucket(self.bucket_name)
            print(f"Using existing bucket: {self.bucket_name}")
        except Exception:
            print(f"Creating new bucket: {self.bucket_name}")
            self.bucket = self.client.create_bucket(self.bucket_name)
    
    def _get_local_path(self, filename):
        """Get path for local file storage"""
        return os.path.join('data_cache', filename)
    
    def _read_local_csv(self, filename):
        """Read data from local CSV file"""
        try:
            filepath = self._get_local_path(filename)
            if not os.path.exists(filepath):
                print(f"Local file not found: {filepath}")
                return []
            
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                data = [OrderedDict([
                    ('timestamp', row['timestamp']),
                    ('severes', int(row['severes'])),
                    ('warnings', int(row['warnings'])),
                    ('alerts', int(row['alerts']))
                ]) for row in reader]
                print(f"Read {len(data)} records from local file: {filepath}")
                return data
        except Exception as e:
            print(f"Error reading local CSV: {e}")
            return []
    
    def _write_local_csv(self, filename, data):
        """Write data to local CSV file"""
        try:
            filepath = self._get_local_path(filename)
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'severes', 'warnings', 'alerts'])
                writer.writeheader()
                writer.writerows(data)
            print(f"Wrote {len(data)} records to local file: {filepath}")
        except Exception as e:
            print(f"Error writing local CSV: {e}")
    
    def _read_csv(self, filename):
        """Read data from CSV file"""
        if hasattr(self, 'use_local_storage'):
            return self._read_local_csv(filename)
        
        try:
            blob = self.bucket.blob(filename)
            if not blob.exists():
                print(f"GCS blob not found: {filename}")
                return []
            
            content = blob.download_as_string().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            data = [OrderedDict([
                ('timestamp', row['timestamp']),
                ('severes', int(row['severes'])),
                ('warnings', int(row['warnings'])),
                ('alerts', int(row['alerts']))
            ]) for row in reader]
            print(f"Read {len(data)} records from GCS: {filename}")
            return data
        except Exception as e:
            print(f"Error reading GCS CSV: {e}")
            return []
    
    def _write_csv(self, filename, data):
        """Write data to CSV file"""
        if hasattr(self, 'use_local_storage'):
            return self._write_local_csv(filename, data)
        
        try:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['timestamp', 'severes', 'warnings', 'alerts'])
            writer.writeheader()
            writer.writerows(data)
            
            blob = self.bucket.blob(filename)
            blob.upload_from_string(output.getvalue(), content_type='text/csv')
            print(f"Wrote {len(data)} records to GCS: {filename}")
        except Exception as e:
            print(f"Error writing GCS CSV: {e}")
    
    def _validate_data_structure(self, data):
        """Validate data structure and format timestamps"""
        if not isinstance(data, list):
            print("Error: Data is not a list")
            return False
        
        required_fields = ['timestamp', 'severes', 'warnings', 'alerts']
        
        for item in data:
            if not all(field in item for field in required_fields):
                print(f"Error: Missing required fields in item: {item}")
                return False
            
            try:
                # Validate timestamp format
                datetime.fromisoformat(item['timestamp'])
                # Validate numeric fields
                if not all(isinstance(item[field], (int, float)) for field in ['severes', 'warnings', 'alerts']):
                    print(f"Error: Invalid numeric fields in item: {item}")
                    return False
            except ValueError as e:
                print(f"Error: Invalid timestamp format in item: {item}")
                return False
            except Exception as e:
                print(f"Error validating data structure: {e}")
                return False
        
        return True

    def _validate_date_range(self, start_date, end_date):
        """Validate date range parameters"""
        try:
            if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
                raise ValueError("Start and end dates must be datetime objects")
            
            if start_date > end_date:
                raise ValueError("Start date cannot be after end date")
            
            if end_date > datetime.now():
                print("Warning: End date is in the future")
            
            max_range = timedelta(days=365)
            if end_date - start_date > max_range:
                print("Warning: Date range exceeds 365 days")
            
            return True
        except Exception as e:
            print(f"Error validating date range: {e}")
            return False

    def store_counts(self, timestamp, data):
        """Store flood counts"""
        try:
            current_month = timestamp[:7]  # YYYY-MM
            filename = f"flood_data_{current_month}.csv"
            
            # Read existing data
            existing_data = self._read_csv(filename)
            
            # Add new data
            new_data = OrderedDict([
                ('timestamp', timestamp),
                ('severes', data['severes']),
                ('warnings', data['warnings']),
                ('alerts', data['alerts'])
            ])
            
            # Remove existing entry for same timestamp if exists
            existing_data = [d for d in existing_data if d['timestamp'] != timestamp]
            existing_data.append(new_data)
            
            # Sort by timestamp
            existing_data.sort(key=lambda x: x['timestamp'])
            
            # Write data
            self._write_csv(filename, existing_data)
            print(f"Successfully stored counts for {timestamp}")
            
        except Exception as e:
            print(f"Error storing counts: {e}")
    
    def get_latest_counts(self):
        """Get the most recent flood counts"""
        try:
            current_month = datetime.now().strftime("%Y-%m")
            filename = f"flood_data_{current_month}.csv"
            
            data = self._read_csv(filename)
            if not data:
                return OrderedDict([
                    ('timestamp', datetime.now().isoformat()),
                    ('severes', 0),
                    ('warnings', 0),
                    ('alerts', 0)
                ])
            
            latest = data[-1]
            print(f"Retrieved latest counts for {latest['timestamp']}")
            return latest
        except Exception as e:
            print(f"Error getting latest counts: {e}")
            return OrderedDict([
                ('timestamp', datetime.now().isoformat()),
                ('severes', 0),
                ('warnings', 0),
                ('alerts', 0)
            ])
    
    def get_counts_between_dates(self, start_date, end_date):
        """Get flood counts between two dates with improved error handling"""
        try:
            print(f"Validating date range: {start_date} to {end_date}")
            if not self._validate_date_range(start_date, end_date):
                raise ValueError("Invalid date range")

            # Generate list of months between start and end date
            current = datetime(start_date.year, start_date.month, 1)
            end = datetime(end_date.year, end_date.month, 1)
            months = []
            
            while current <= end:
                months.append(current.strftime("%Y-%m"))
                if current.month == 12:
                    current = datetime(current.year + 1, 1, 1)
                else:
                    current = datetime(current.year, current.month + 1, 1)
            
            print(f"Processing data for months: {months}")
            
            # Collect data from all relevant months
            all_data = []
            for month in months:
                filename = f"flood_data_{month}.csv"
                try:
                    monthly_data = self._read_csv(filename)
                    if monthly_data:
                        print(f"Found {len(monthly_data)} records for {month}")
                        all_data.extend(monthly_data)
                    else:
                        print(f"No data found for {month}")
                except Exception as e:
                    print(f"Error reading data for {month}: {e}")
            
            if not all_data:
                print("No data found for the entire date range")
                return self._create_default_response()
            
            # Validate data structure
            if not self._validate_data_structure(all_data):
                raise ValueError("Invalid data structure detected")
            
            # Filter by date range
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()
            filtered_data = [
                d for d in all_data 
                if start_str <= d['timestamp'] <= end_str
            ]
            
            # Sort and validate final dataset
            filtered_data.sort(key=lambda x: x['timestamp'])
            print(f"Found {len(filtered_data)} records between {start_str} and {end_str}")
            
            if not filtered_data:
                return self._create_default_response()
            
            return filtered_data
            
        except Exception as e:
            print(f"Error in get_counts_between_dates: {str(e)}")
            print("Stack trace:", traceback.format_exc())
            return self._create_default_response()
    
    def _create_default_response(self):
        """Create a default response for error cases"""
        return [OrderedDict([
            ('timestamp', datetime.now().isoformat()),
            ('severes', 0),
            ('warnings', 0),
            ('alerts', 0)
        ])]