from curl_cffi import requests
from bs4 import BeautifulSoup
import re

# 1. Croma
url_croma = 'https://www.croma.com/searchB?q=laptop%3Arelevance&text=laptop'
r_cr = requests.get(url_croma, impersonate='chrome124', timeout=15)
soup_cr = BeautifulSoup(r_cr.text, 'lxml')
print('Croma title:', soup_cr.title.text if soup_cr.title else 'None')
cr_items = soup_cr.select('.product-item, .cp-product, li.product-item, div.product-info')
print('Croma product items:', len(cr_items))
if not cr_items:
    # check links
    cr_links = [a['href'] for a in soup_cr.find_all('a', href=True) if '/p/' in a['href']]
    print('Croma /p/ links:', len(cr_links))
    if cr_links:
        print('Sample Croma link:', cr_links[0])

# 2. Vijay Sales
import requests as req
url_vs = 'https://www.vijaysales.com/search/laptop'
r_vs = req.get(url_vs, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=15)
soup_vs = BeautifulSoup(r_vs.text, 'lxml')
print('\nVijay Sales title:', soup_vs.title.text if soup_vs.title else 'None')
vs_items = soup_vs.select('.vj-product-card, .Dynamic-Product-Card, .product-card, .vj-prod-box')
print('Vijay Sales items:', len(vs_items))
if not vs_items:
    vs_links = [a['href'] for a in soup_vs.find_all('a', href=True) if '/p/' in a['href'] or '/product/' in a['href']]
    print('Vijay Sales links:', len(vs_links))
