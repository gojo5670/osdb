from flask import Flask, request, jsonify
from pymongo import MongoClient
import requests
import os

# ========== CONFIG ========== #
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "lund"
COLLECTION_NAME = "chut"

BOT_TOKEN = "7940557712:AAHYHp4-jJYiuxbsMiANao8CnVrEz7ak-nc"
CHAT_ID = "1074750898"

# ========== INIT ========== #
app = Flask(__name__)
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ========== UTILS ========== #
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram error:", e)

def clean_result(doc):
    doc.pop("_id", None)
    return doc

def expand_and_fetch(initial_results):
    seen_ids = set()
    search_values = set()

    for doc in initial_results:
        if "mobile" in doc:
            search_values.add(doc["mobile"])
        if "alt" in doc:
            search_values.add(doc["alt"])
        if "id" in doc:
            search_values.add(doc["id"])

    if not search_values:
        return []

    expanded_query = {
        "$or": [
            {"mobile": {"$in": list(search_values)}},
            {"alt": {"$in": list(search_values)}},
            {"id": {"$in": list(search_values)}}
        ]
    }

    expanded_results = []
    for doc in collection.find(expanded_query):
        doc_id = str(doc.get("_id"))
        if doc_id not in seen_ids:
            seen_ids.add(doc_id)
            expanded_results.append(clean_result(doc))

    return expanded_results

# ========== ROUTES ========== #
@app.route("/search/mobile", methods=["GET"])
def search_by_mobile():
    number = request.args.get("value")
    if not number:
        return jsonify({"error": "Missing mobile number"}), 400

    initial_query = {"$or": [{"mobile": number}, {"alt": number}]}
    initial_results = list(collection.find(initial_query))

    if not initial_results:
        send_telegram(f"❌ Mobile search for <b>{number}</b> returned 0 results.")
        return jsonify({"error": "No records found"}), 404

    full_results = expand_and_fetch(initial_results)
    send_telegram(f"📱 Mobile search for <b>{number}</b> returned {len(full_results)} results.")
    return jsonify(full_results), 200

@app.route("/search/id", methods=["GET"])
def search_by_id():
    user_id = request.args.get("value")
    if not user_id:
        return jsonify({"error": "Missing ID"}), 400

    initial_query = {"id": user_id}
    initial_results = list(collection.find(initial_query))

    if not initial_results:
        send_telegram(f"❌ ID search for <b>{user_id}</b> returned 0 results.")
        return jsonify({"error": "No records found"}), 404

    full_results = expand_and_fetch(initial_results)
    send_telegram(f"🆔 ID search for <b>{user_id}</b> returned {len(full_results)} results.")
    return jsonify(full_results), 200

@app.route("/search/email", methods=["GET"])
def search_by_email():
    email = request.args.get("value")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    initial_query = {"email": email}
    initial_results = list(collection.find(initial_query))

    if not initial_results:
        send_telegram(f"❌ Email search for <b>{email}</b> returned 0 results.")
        return jsonify({"error": "No records found"}), 404

    full_results = expand_and_fetch(initial_results)
    send_telegram(f"✉️ Email search for <b>{email}</b> returned {len(full_results)} results.")
    return jsonify(full_results), 200

@app.route("/", methods=["GET"])
def root():
    return "✅ API is live.", 200

# ========== MAIN ========== #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
