import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
from bs4 import BeautifulSoup
from src.data.scraper.base import BaseScraper
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}
s = requests.Session()
s.headers.update(headers)
r = s.get('https://www.flipkart.com/search?q=laptop&page=1', timeout=15)
soup = BeautifulSoup(r.text, 'lxml')
cards = soup.select('div[data-id]')

INR_TO_USD = 0.012

class DummyScraper(BaseScraper):
    def scrape(self, max_products=10): return []

d = DummyScraper('Flipkart')

rows = []
for card in cards[:5]:
    # Extract title
    title = ''
    img = card.select_one('img[alt]')
    if img and img.get('alt'):
        title = img.get('alt').strip()
    if not title:
        title_el = card.select_one('div.KzDlHZ, div._4rR01T, a[title]')
        if title_el:
            title = title_el.text.strip()
    if not title:
        continue
        
    card_text = card.get_text(separator=' | ')
    price_m = re.search(r'₹\s*([\d,]+)', card_text)
    if not price_m:
        continue
    price_inr = price_m.group(1).replace(',', '')
    
    bullets = [li.text.strip() for li in card.select('ul.G4BRas li, ul._1xgFaf li, li')]
    link = card.select_one('a[href*="/p/"]')
    href = 'https://www.flipkart.com' + link['href'].split('?')[0] if link and 'href' in link.attrs else ''
    
    row = d.empty_row()
    row['source'] = 'Flipkart'
    row['model_name'] = title
    row['url'] = href
    row['price_original'] = price_inr
    row['currency'] = 'INR'
    row['price_usd'] = f"{float(price_inr) * INR_TO_USD:.2f}"
    
    for b in bullets:
        b_low = b.lower()
        if any(k in b_low for k in ['processor', 'core', 'ryzen']):
            cpu_d = d.parse_cpu_string(b)
            for k, v in cpu_d.items():
                if v: row[k] = v
        if 'ram' in b_low:
            r_gb, r_type = d.parse_ram(b)
            if r_gb: row['ram_gb'] = r_gb
            if r_type: row['ram_type'] = r_type
        if any(k in b_low for k in ['ssd', 'hdd', 'emmc']):
            cap, stype, sec = d.parse_storage(b)
            if cap: row['storage_capacity_gb'] = cap
            if stype: row['storage_type'] = stype
            if sec: row['secondary_storage_gb'] = sec
        if any(k in b_low for k in ['display', 'inch', 'cm']):
            sz_m = re.search(r'(\d{1,2}(?:\.\d{1,2})?)\s*(?:inch|cm\s*\(([\d.]+)\s*inch)', b, re.IGNORECASE)
            if sz_m:
                row['screen_size_inches'] = sz_m.group(2) if sz_m.group(2) else sz_m.group(1)
        if any(k in b_low for k in ['operating system', 'windows', 'chrome']):
            if 'windows 11' in b_low: row['operating_system'] = 'Windows 11'
            elif 'windows 10' in b_low: row['operating_system'] = 'Windows 10'
            elif 'chrome' in b_low: row['operating_system'] = 'Chrome OS'
            
    combined = f"{title} {' '.join(bullets)}"
    d.parse_title_features(combined, row)
    rows.append(row)

print(f"Parsed {len(rows)} rows successfully.")
for i, r in enumerate(rows):
    print(f"\n--- Laptop {i+1} ---")
    for k in ['brand', 'model_name', 'cpu_brand', 'cpu_family', 'cpu_model', 'cpu_generation', 'ram_gb', 'ram_type', 'storage_capacity_gb', 'storage_type', 'screen_size_inches', 'screen_resolution', 'gpu_brand', 'gpu_model', 'gpu_generation', 'operating_system', 'price_original', 'price_usd']:
        val = str(r[k]).encode('ascii', 'replace').decode()
        print(f"  {k:20s}: {val[:60]}")
