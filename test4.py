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

# Function to generate a unique filename
def generate_filename(prefix="receipt"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.csv"

# Read an image
image = cv2.imread('receipt3.png')

# Convert it into text
text = (pytesseract.image_to_string(image)).lower()
print(text)

# Identify the date
match = re.findall(r'\d+[/.-]\d+[/.-]\d+', text)
date_str = " ".join(match)
print(date_str)

nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)

# Extract title
sent_tokens = nltk.sent_tokenize(text)
head = sent_tokens[0].splitlines()[0]  # Assuming the title is the first line of the first sentence
print(head)

# Find the price of the category
price = re.findall(r'[\$\£\€](\d+(?:\.\d{1,2})?)', text)
price = list(map(float, price))
max_price = max(price) if price else 0
print(max_price)

# Tokenize the text
print(word_tokenize(text))
tokenizer = nltk.RegexpTokenizer(r"\w+")
new_words = tokenizer.tokenize(text)
print(new_words)

# Filter stop words
nltk.download('stopwords', quiet=True)
stop_words = set(nltk.corpus.stopwords.words('english'))
filtered_list = [w for w in new_words if w not in stop_words]
print(filtered_list)

# Prepare to write to the new CSV file
new_filename = generate_filename()

# Extract line items from the receipt text
lines = text.split('\n')
line_items = []
for line in lines:
    item_match = re.match(r'(.+?)\s+([\$\£\€]\d+(?:\.\d{1,2})?)', line)
    if item_match:
        item_name = item_match.group(1).strip()
        item_price = float(item_match.group(2)[1:])  # Remove the currency symbol and convert to float
        line_items.append((date_str, item_name, item_price))

# Function to write rows to a new CSV file
def write_rows_to_csv(file, rows):
    with open(file, 'w', newline='') as write_obj:
        csv_writer = csv.writer(write_obj)
        csv_writer.writerow(['Date', 'Item', 'Amount'])
        csv_writer.writerows(rows)

write_rows_to_csv(new_filename, line_items)

# Load and process the new CSV file
def load_and_process_csv(filename):
    if os.path.isfile(filename):
        df = pd.read_csv(filename)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        return pd.DataFrame(columns=['Date', 'Item', 'Amount'])

dataframe = load_and_process_csv(new_filename)

# Display the head of the dataframe
print(dataframe.head())
