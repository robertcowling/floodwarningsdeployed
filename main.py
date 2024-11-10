from flask import Flask, render_template, jsonify, request, Response
from flask.json.provider import DefaultJSONProvider
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import flood_service
import database
import json
from collections import OrderedDict
import gzip
from functools import wraps

class OrderedJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        # Ensure that the order is preserved during JSON serialization
        kwargs['sort_keys'] = False
        return super().dumps(obj, **kwargs)

    def default(self, obj):
        if isinstance(obj, OrderedDict):
            return dict(obj)
        return super().default(obj)

def gzipped(f):
    @wraps(f)
    def view_func(*args, **kwargs):
        # Check if client accepts gzip encoding
        if 'gzip' not in request.accept_encodings:
            return f(*args, **kwargs)

        response = f(*args, **kwargs)
        
        # If response is not already a Response object, convert it
        if not isinstance(response, Response):
            response = jsonify(response)

        # Compress the response data
        gzip_buffer = gzip.compress(response.get_data())
        
        # Create new response with compressed data
        response.set_data(gzip_buffer)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(gzip_buffer)
        response.headers['Vary'] = 'Accept-Encoding'
        return response
    return view_func

app = Flask(__name__)
app.json = OrderedJSONProvider(app)

# Initialize the scheduler with timezone awareness
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=flood_service.fetch_and_store_flood_data, 
    trigger="cron", 
    minute="*/15",  # Run exactly at 0, 15, 30, 45 minutes
    id='fetch_flood_data'
)
scheduler.start()

@app.route('/')
def index():
    """Render the trend page (new homepage)"""
    return render_template('trend.html')

@app.route('/current')
def current():
    """Render the current warnings status page"""
    return render_template('current.html')

@app.route('/api')
def api_docs():
    """Render the API documentation page"""
    return render_template('api.html')

@app.route('/api/current')
@gzipped
def get_current_counts():
    """Get the most recent flood counts"""
    current_data = database.get_latest_counts()
    return jsonify(current_data)

@app.route('/api/historical')
@gzipped
def get_historical_data():
    """Get historical flood counts between two dates"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)  # Default to last 24 hours
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    
    if 'start_date' in request.args:
        start_date = datetime.strptime(request.args['start_date'], '%Y-%m-%d')
    if 'end_date' in request.args:
        end_date = datetime.strptime(request.args['end_date'], '%Y-%m-%d')
    
    historical_data = database.get_counts_between_dates(start_date, end_date, page, per_page)
    return jsonify(historical_data)

@app.route('/api/summary')
@gzipped
def get_summary():
    """Get summary statistics of flood events"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Last week summary
    
    data = database.get_counts_between_dates(start_date, end_date)
    
    if not data:
        return jsonify(OrderedDict([
            ('max_alerts', 0),
            ('max_warnings', 0),
            ('max_severes', 0),
            ('avg_alerts', 0),
            ('avg_warnings', 0),
            ('avg_severes', 0),
        ]))
    
    summary = OrderedDict([
        ('max_alerts', max(item['alerts'] for item in data)),
        ('max_warnings', max(item['warnings'] for item in data)),
        ('max_severes', max(item['severes'] for item in data)),
        ('avg_alerts', round(sum(item['alerts'] for item in data) / len(data), 2)),
        ('avg_warnings', round(sum(item['warnings'] for item in data) / len(data), 2)),
        ('avg_severes', round(sum(item['severes'] for item in data) / len(data), 2)),
    ])
    
    return jsonify(summary)

if __name__ == '__main__':
    # Fetch initial data
    flood_service.fetch_and_store_flood_data()
    app.run(host='0.0.0.0', port=5000)
