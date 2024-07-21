from PIL import Image
import pytesseract
import cv2
import os
import pandas as pd
import csv
import nltk
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from datetime import datetime

def generate_filename(prefix="receipt"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.csv"


image = cv2.imread('1057-receipt.jpg')

text = (pytesseract.image_to_string(image)).lower()
print(text)

match = re.findall(r'\d+[/.-]\d+[/.-]\d+', text)
date_str = " ".join(match)
print("the date is:",date_str)

nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)

sent_tokens = nltk.sent_tokenize(text)
head = sent_tokens[0].splitlines()[0] 
print(head)

price = re.findall(r'[\$\£\€](\d+(?:\.\d{1,2})?)', text)
price = list(map(float, price))
max_price = max(price) if price else 0
print(max_price)



new_filename = generate_filename()

lines = text.split('\n')
line_items = []
for line in lines:
    item_match = re.match(r'(.+?)\s+([\$\£\€]\d+(?:\.\d{1,2})?)', line)
    if item_match:
        item_name = item_match.group(1).strip()
        item_price = float(item_match.group(2)[1:])  
        line_items.append((date_str, item_name, item_price))

def write_rows_to_csv(file, rows):
    with open(file, 'w', newline='') as write_obj:
        csv_writer = csv.writer(write_obj)
        csv_writer.writerow(['Date', 'Item', 'Amount'])
        csv_writer.writerows(rows)

write_rows_to_csv(new_filename, line_items)

def load_and_process_csv(filename):
    if os.path.isfile(filename):
        df = pd.read_csv(filename)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        return pd.DataFrame(columns=['Date', 'Item', 'Amount'])

dataframe = load_and_process_csv(new_filename)

print(dataframe.head())


