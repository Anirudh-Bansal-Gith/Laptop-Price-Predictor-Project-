import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
from bs4 import BeautifulSoup
from src.data.scraper.base import BaseScraper
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}
s = requests.Session()
s.headers.update(headers)
r = s.get('https://www.amazon.in/s?k=laptop&page=1', timeout=15)
soup = BeautifulSoup(r.text, 'lxml')
cards = soup.select('div[data-component-type="s-search-result"]')

class DummyScraper(BaseScraper):
    def scrape(self, max_products=10): return []

d = DummyScraper('Amazon')

rows = []
for c in cards[:5]:
    h2 = c.select_one('h2')
    if not h2: continue
    title = h2.text.strip()
    
    price_el = c.select_one('span.a-price-whole')
    if not price_el: continue
    price_str = price_el.text.strip().replace(',', '')
    
    asin = c.get('data-asin', '')
    url = f"https://www.amazon.in/dp/{asin}" if asin else ""
    
    row = d.empty_row()
    row['source'] = 'Amazon'
    row['model_name'] = title
    row['url'] = url
    row['price_original'] = price_str
    row['currency'] = 'INR'
    try:
        row['price_usd'] = f"{float(price_str) * 0.012:.2f}"
    except ValueError:
        pass
        
    d.parse_title_features(title, row)
    rows.append(row)

print(f"Extracted {len(rows)} Amazon rows:")
for i, r in enumerate(rows):
    print(f"\n--- Amazon {i+1} ---")
    for k in ['brand', 'model_name', 'cpu_brand', 'cpu_family', 'cpu_model', 'cpu_generation', 'ram_gb', 'ram_type', 'storage_capacity_gb', 'storage_type', 'screen_size_inches', 'gpu_brand', 'gpu_model', 'gpu_generation', 'operating_system', 'price_original', 'price_usd']:
        val = str(r[k]).encode('ascii', 'replace').decode()
        print(f"  {k:20s}: {val[:55]}")
