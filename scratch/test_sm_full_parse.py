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
r = s.get('https://www.smartprix.com/laptops', timeout=15)
soup = BeautifulSoup(r.text, 'lxml')
items = soup.select('div.sm-product')

class DummyScraper(BaseScraper):
    def scrape(self, max_products=10): return []

d = DummyScraper('Smartprix')

rows = []
for item in items[:5]:
    name_el = item.select_one('h2, .name, a[title]')
    if not name_el: continue
    title = name_el.text.strip()
    
    price_el = item.select_one('.price')
    if not price_el: continue
    price_clean = re.sub(r'[^\d]', '', price_el.text.strip())
    if not price_clean: continue
    
    link_el = item.select_one('a[href*="/laptops/"]')
    href = 'https://www.smartprix.com' + link_el['href'] if link_el and 'href' in link_el.attrs else ''
    
    features = [li.text.strip() for li in item.select('ul.features li, ul li')]
    
    row = d.empty_row()
    row['source'] = 'Smartprix'
    row['model_name'] = title
    row['url'] = href
    row['price_original'] = price_clean
    row['currency'] = 'INR'
    try:
        row['price_usd'] = f"{float(price_clean) * 0.012:.2f}"
    except ValueError:
        pass
        
    for feat in features:
        f_low = feat.lower()
        if any(k in f_low for k in ['core', 'ryzen', 'snapdragon', 'intel', 'amd', 'm1', 'm2', 'm3', 'm4', 'processor', 'gen ']):
            if not any(k in f_low for k in ['graphics', 'rtx', 'gtx', 'geforce', 'radeon']):
                cpu_d = d.parse_cpu_string(feat)
                for k, v in cpu_d.items():
                    if v: row[k] = v
        if 'cores' in f_low or 'core,' in f_low:
            c_m = re.search(r'(\d+)\s*Cores?', feat, re.IGNORECASE)
            if c_m: row['cpu_cores'] = c_m.group(1)
            elif 'octa core' in f_low: row['cpu_cores'] = '8'
            elif 'hexa core' in f_low: row['cpu_cores'] = '6'
            elif 'quad core' in f_low: row['cpu_cores'] = '4'
        if 'ram' in f_low:
            r_gb, r_type = d.parse_ram(feat)
            if r_gb: row['ram_gb'] = r_gb
            if r_type: row['ram_type'] = r_type
        if any(k in f_low for k in ['ssd', 'hdd', 'emmc']):
            cap, stype, sec = d.parse_storage(feat)
            if cap: row['storage_capacity_gb'] = cap
            if stype: row['storage_type'] = stype
            if sec: row['secondary_storage_gb'] = sec
        if any(k in f_low for k in ['rtx', 'gtx', 'geforce', 'radeon', 'iris', 'uhd', 'graphics', 'arc ']):
            gpu_d = d.parse_gpu_string(feat)
            for k, v in gpu_d.items():
                if v: row[k] = v
        if 'inches' in f_low or 'pixels' in f_low or 'resolution' in f_low:
            sz_m = re.search(r'(\d{1,2}(?:\.\d{1,2})?)\s*inches?', feat, re.IGNORECASE)
            if sz_m: row['screen_size_inches'] = sz_m.group(1)
            res_m = re.search(r'(\d{3,4}\s*[xX*×]\s*\d{3,4})', feat)
            if res_m: row['screen_resolution'] = re.sub(r'\s*', '', res_m.group(1)).replace('X', 'x')

    combined = f"{title} {' '.join(features)}"
    d.parse_title_features(combined, row)
    rows.append(row)

print(f"Parsed {len(rows)} Smartprix rows:")
for i, r in enumerate(rows):
    print(f"\n--- Smartprix {i+1} ---")
    for k in ['brand', 'model_name', 'cpu_brand', 'cpu_family', 'cpu_model', 'cpu_generation', 'cpu_cores', 'ram_gb', 'ram_type', 'storage_capacity_gb', 'storage_type', 'screen_size_inches', 'screen_resolution', 'gpu_brand', 'gpu_model', 'gpu_generation', 'gpu_vram_gb', 'operating_system', 'price_original', 'price_usd']:
        val = str(r[k]).encode('ascii', 'replace').decode()
        print(f"  {k:20s}: {val[:55]}")
