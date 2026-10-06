import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}
s = requests.Session()
s.headers.update(headers)

r = s.get('https://www.smartprix.com/laptops', timeout=15)
soup = BeautifulSoup(r.text, 'lxml')
items = soup.select('div.sm-product, div.item, div.product-card, div[data-item]')
print(f"Smartprix items found: {len(items)}")
if not items:
    # Look for any product links or containers
    links = [a for a in soup.find_all('a', href=True) if '/laptops/' in a['href'] and a['href'] != '/laptops']
    print(f"Smartprix product links: {len(links)}")
    for l in links[:5]:
        print(" ", l['href'], "| Text:", l.text.strip()[:50])
