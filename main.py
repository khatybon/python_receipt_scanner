from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import cv2
import os
import pandas as pd
import csv
import nltk
import re
from datetime import datetime
from flask_cors import CORS
import uuid
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)

app = Flask(__name__)
CORS(app)

def generate_filename(prefix="receipt"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.csv"

def process_image(image_path):
    image = cv2.imread(image_path)
    text = pytesseract.image_to_string(image).lower()
    if not text:
        print(f"No text found in {image_path}")
        return []

    lines = text.split('\n')
    line_items = []
    total_price = 0
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 3:
            item_name = ' '.join(parts[:-2])  
            try:
                quantity = int(parts[-2])
                price = float(parts[-1].replace('$', ''))
                line_items.append((item_name, quantity, price))
                total_price += price * quantity
            except ValueError:
                continue

    line_items.append(('Total', '', total_price))

    return line_items

def write_rows_to_csv(file, rows):
    with open(file, 'w', newline='') as write_obj:
        csv_writer = csv.writer(write_obj)
        csv_writer.writerow(['Item', 'Quantity', 'Price'])
        csv_writer.writerows(rows)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = file.filename
        file_path = os.path.join('uploads', f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        line_items = process_image(file_path)
        output_filename = generate_filename()
        write_rows_to_csv(output_filename, line_items)
        data = csv_to_json(output_filename)
        return jsonify(data)

def csv_to_json(filepath):
    data = []
    with open(filepath, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)
    return data

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
