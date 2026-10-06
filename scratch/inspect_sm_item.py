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
items = soup.select('div.sm-product')

for item in items[:3]:
    name_el = item.select_one('h2, .name, a[title]')
    price_el = item.select_one('.price')
    features = [li.text.strip() for li in item.select('ul.features li, ul li')]
    print("-----------------------------------------")
    print("Name:", name_el.text.strip() if name_el else "None")
    print("Price:", price_el.text.strip().encode('ascii', 'replace').decode() if price_el else "None")
    print("Features:", features[:6])
