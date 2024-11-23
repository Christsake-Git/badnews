from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import json
import requests
import time
from datetime import datetime  # Import datetime module

app = Flask(__name__)

# File paths
VENDORS_FILE = 'vendors.csv'
BAD_NEWS_FILE = 'bad_news.json'
API_USAGE_FILE = 'api_usage.json'

# Initialize files if they do not exist
def initialize_files():
    if not os.path.exists(VENDORS_FILE):
        with open(VENDORS_FILE, 'w') as f:
            f.write("vendor\n")  # Create a CSV with a header

    if not os.path.exists(BAD_NEWS_FILE):
        with open(BAD_NEWS_FILE, 'w') as f:
            json.dump({}, f)  # Create an empty JSON file

    if not os.path.exists(API_USAGE_FILE):
        with open(API_USAGE_FILE, 'w') as f:
            json.dump({"usage_count": 0}, f)  # Initialize API usage count

initialize_files()

def load_vendors():
    """Load vendors from a CSV file."""
    df = pd.read_csv(VENDORS_FILE)
    return df['vendor'].tolist()

def save_vendors(vendors):
    """Save vendors to a CSV file."""
    df = pd.DataFrame(vendors, columns=['vendor'])
    df.to_csv(VENDORS_FILE, index=False)

def load_bad_news():
    """Load bad news from a JSON file."""
    with open(BAD_NEWS_FILE, 'r') as f:
        return json.load(f)

def save_bad_news(bad_news):
    """Save bad news to a JSON file."""
    with open(BAD_NEWS_FILE, 'w') as f:
        json.dump(bad_news, f)

def load_api_usage():
    """Load API usage from a JSON file."""
    with open(API_USAGE_FILE, 'r') as f:
        return json.load(f)

def save_api_usage(usage_count):
    """Save API usage to a JSON file."""
    with open(API_USAGE_FILE, 'w') as f:
        json.dump({"usage_count": usage_count}, f)

def google_search(vendor):
    """Perform a Google search for the vendor."""
    search_url = f"https://www.google.com/search?as_q={vendor}&as_oq=cyber+attack+or+data+breach+or+negative+news+or+%22data+breach%22+or+fraud+or+scam&as_qdr=d"
    attempts = 0
    while attempts < 5:
        try:
            response = requests.get(search_url)
            if response.status_code == 200:
                return response.text  # Return the HTML content of the search results
            elif response.status_code == 429:
                attempts += 1
                time.sleep(2 ** attempts)  # Exponential backoff
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    return None

@app.route('/vendors', methods=['GET'])
def get_vendors():
    vendors = load_vendors()
    return jsonify(vendors)

@app.route('/manage_vendors', methods=['POST'])
def manage_vendors():
    data = request.json
    action = data.get('action')
    vendor_name = data.get('vendor')

    vendors = load_vendors()

    if action == 'add' and vendor_name not in vendors:
        vendors.append(vendor_name)
        save_vendors(vendors)
        return jsonify({"message": f"Vendor '{vendor_name}' added."}), 201
    elif action == 'delete' and vendor_name in vendors:
        vendors.remove(vendor_name)
        save_vendors(vendors)
        return jsonify({"message": f"Vendor '{vendor_name}' removed."}), 200
    else:
        return jsonify({"message": "Invalid action or vendor not found."}), 400

@app.route('/force_scan', methods=['POST'])
def force_scan():
    vendors = load_vendors()
    bad_news = {}
    api_usage = load_api_usage()
    usage_count = api_usage['usage_count']

    for vendor in vendors:
        search_results = google_search(vendor)
        if search_results:
            bad_news[vendor] = search_results
        else:
            bad_news[vendor] = "No results found."

    usage_count += len(vendors)  # Increment usage count by the number of vendors scanned
    save_api_usage(usage_count)  # Corrected line
    save_bad_news(bad_news)      # Corrected line

    return jsonify({"message": "Scan completed successfully."}), 200

@app.route('/badnews', methods=['GET'])
def bad_news_view():
    bad_news = load_bad_news()
    last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    api_usage = load_api_usage()
    usage_count = api_usage['usage_count']

    return render_template('index.html', bad_news=bad_news, last_scan_time=last_scan_time, usage_count=usage_count)

if __name__ == '__main__':
    app.run(debug=True)
