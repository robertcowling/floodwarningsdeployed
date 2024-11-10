from flask import Flask, render_template, jsonify, request, abort
from flask.json.provider import DefaultJSONProvider
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import flood_service
import database
import json
from collections import OrderedDict

class OrderedJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs['sort_keys'] = False
        return super().dumps(obj, **kwargs)

    def default(self, obj):
        if isinstance(obj, OrderedDict):
            return dict(obj)
        return super().default(obj)

app = Flask(__name__)
app.json = OrderedJSONProvider(app)

# Initialize the scheduler with timezone awareness
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=flood_service.fetch_and_store_flood_data, 
    trigger="cron", 
    minute="*/15",
    id='fetch_flood_data'
)
scheduler.start()

@app.route('/')
def index():
    """Render the main page with API documentation and demos"""
    return render_template('index.html')

@app.route('/historical')
def historical():
    """Render the historical data page"""
    return render_template('historical.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/api/current')
def get_current_counts():
    """Get the most recent flood counts"""
    try:
        current_data = database.get_latest_counts()
        return jsonify(current_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/historical')
def get_historical_data():
    """Get historical flood counts between two dates"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)  # Default to last 3 days
        
        if 'start_date' in request.args:
            start_date = datetime.strptime(request.args['start_date'], '%Y-%m-%d')
        if 'end_date' in request.args:
            end_date = datetime.strptime(request.args['end_date'], '%Y-%m-%d')
        
        historical_data = database.get_counts_between_dates(start_date, end_date)
        return jsonify(historical_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/summary')
def get_summary():
    """Get summary statistics of flood events"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last week summary
        
        data = database.get_counts_between_dates(start_date, end_date)
        
        summary = OrderedDict([
            ('max_alerts', max(item['alerts'] for item in data)),
            ('max_warnings', max(item['warnings'] for item in data)),
            ('max_severes', max(item['severes'] for item in data)),
            ('avg_alerts', sum(item['alerts'] for item in data) / len(data)),
            ('avg_warnings', sum(item['warnings'] for item in data) / len(data)),
            ('avg_severes', sum(item['severes'] for item in data) / len(data)),
        ])
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Fetch initial data
    flood_service.fetch_and_store_flood_data()
    app.run(host='0.0.0.0', port=5000)
