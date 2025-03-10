from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='.')
CORS(app)  # Aktiviere CORS für alle Routen

# Speicherort für die Zahlungsdaten
PAYMENTS_FILE = "payments.json"

def load_payments():
    if os.path.exists(PAYMENTS_FILE):
        with open(PAYMENTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_payment(payment_data):
    payments = load_payments()
    payments.append(payment_data)
    with open(PAYMENTS_FILE, 'w') as f:
        json.dump(payments, f, indent=4)

@app.route('/')
def index():
    return send_file('pay.html')

@app.route('/purchase', methods=['POST'])
def process_purchase():
    payment_data = request.get_json()
    save_payment(payment_data)  # Save the payment data
    return jsonify({"message": "Payment processed successfully!"}), 200

@app.route('/check-payment', methods=['GET'])
def check_payment():
    payments = load_payments()
    return jsonify({
        "status": "success",
        "total_payments": len(payments),
        "latest_payment": payments[-1] if payments else None
    })

if __name__ == '__main__':
    try:
        print("💰 Payment Server startet...")
        port = 5000
        print(f"📡 Server läuft auf http://localhost:{port}")
        # Deaktiviere den Reloader und Debug-Modus für bessere Stabilität
        app.run(host='127.0.0.1', port=port, debug=False)
    except Exception as e:
        print(f"Fehler beim Starten des Servers: {e}") 