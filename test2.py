from PIL import Image
import pytesseract
import cv2
import os
import pandas as pd
import csv
import nltk
import re
from datetime import datetime
import matplotlib.pyplot as plt

# Ensure NLTK data is downloaded
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)

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
    tax_match = re.search(r'sales tax\s+\(([\d.]+)%\)', text, re.IGNORECASE)
    if tax_match:
        tax_percentage = float(tax_match.group(1))
        total_amount = extract_total_amount(text)
        if total_amount:
            return round((tax_percentage / 100) * total_amount, 2)
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
    total_amount = extract_total_amount(text)
    tax_amount = extract_tax_amount(text)

    for line in lines:
        if "total" in line.lower() or "tax" in line.lower():
            continue
        item_match = re.match(r'(.+?)\s+([\$\£\€]\d+(?:\.\d{1,2})?)', line)
        if item_match:
            item_name = item_match.group(1).strip()
            item_price = float(item_match.group(2)[1:])  
            line_items.append((date_str, head, item_name, item_price, None, None))

    # Add total and tax only once
    if total_amount is not None:
        line_items.append((date_str, head, 'total', 0.0, total_amount, tax_amount))
    if tax_amount is not None:
        line_items.append((date_str, head, 'sales tax', 0.0, None, tax_amount))

    return line_items

def write_rows_to_csv(file, rows):
    with open(file, 'w', newline='') as write_obj:
        csv_writer = csv.writer(write_obj)
        csv_writer.writerow(['date', 'head', 'Item', 'Amount', 'Total', 'Tax'])
        csv_writer.writerows(rows)


# Directory and file handling
output_filename = generate_filename()
all_line_items = []

# Process a single image
image_path = 'images/1007-receipt.jpg'  # Path to the specific image
if os.path.isfile(image_path):
    line_items = process_image(image_path)
    all_line_items.extend(line_items)

# Write all collected data to the CSV file
write_rows_to_csv(output_filename, all_line_items)

# Load and process the new CSV file
def load_and_process_csv(filename):
    if os.path.isfile(filename):
        df = pd.read_csv(filename, encoding='latin1')  # Specify the encoding here
        return df
    else:
        return pd.DataFrame(columns=['date', 'head', 'Item', 'Amount', 'Total', 'Tax'])

dataframe = load_and_process_csv(output_filename)
print(dataframe.head())

filtered_df = dataframe[~dataframe['Item'].isin(['total', 'sales tax'])]
plt.figure(figsize=(24, 5))
plt.bar(filtered_df['head'], filtered_df['Amount'])
plt.xlabel('Head')
plt.ylabel('Amount')
plt.title('Amount by Head')
filtered_df.plot(x='head', y='Amount', kind='barh', title='margin')
plt.show()
