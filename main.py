from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
import cv2
import os
import pandas as pd
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

def generate_filename(prefix="receipt"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.csv"

def extract_total_amount(text):
    total_match = re.search(r'\btotal\s+([\$\£\€]?\d+(?:\.\d{1,2})?)', text, re.IGNORECASE)
    if total_match:
        total_amount = float(total_match.group(1).replace('$', '').replace('£', '').replace('€', ''))
        return total_amount
    return None

def extract_tax_amount(text):
    tax_match = re.search(r'\btax\s+([\$\£\€]?\d+(?:\.\d{1,2})?)', text, re.IGNORECASE)
    if tax_match:
        tax_amount = float(tax_match.group(1).replace('$', '').replace('£', '').replace('€', ''))
        return tax_amount
    return None

def process_image(image_path):
    image = cv2.imread(image_path)
    text = pytesseract.image_to_string(image).lower()
    if not text:
        print(f"No text found in {image_path}")
        return []

    sent_tokens = nltk.sent_tokenize(text)
    head = sent_tokens[0].splitlines()[0] if sent_tokens else "Unknown"

    price = re.findall(r'[\$\£\€](\d+(?:\.\d{1,2})?)', text)
    price = list(map(float, price))
    max_price = max(price) if price else 0

    match = re.findall(r'\d+[/]\d+[/]\d+', text)
    date_str = " ".join(match)

    lines = text.split('\n')
    line_items = []
    total_price = extract_total_amount(text)
    tax_amount = extract_tax_amount(text)

    for line in lines:
        item_match = re.match(r'(.+?)\s+([\$\£\€]\d+(?:\.\d{1,2})?)', line)
        if item_match:
            item_name = item_match.group(1).strip()
            item_price = float(item_match.group(2)[1:])
            line_items.append((date_str, item_name, item_price, total_price, tax_amount))

    return line_items

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = file.filename
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        line_items = process_image(file_path)
        return jsonify(line_items)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
