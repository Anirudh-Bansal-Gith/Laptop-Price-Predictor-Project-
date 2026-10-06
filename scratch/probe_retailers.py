import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}
s = requests.Session()
s.headers.update(headers)

# 1. Vedant Computers
try:
    r_vc = s.get('https://www.vedantcomputers.com/index.php?route=product/search&search=laptop', timeout=15)
    soup_vc = BeautifulSoup(r_vc.text, 'lxml')
    vc_items = soup_vc.select('.product-thumb, .product-layout, div.product-grid')
    print('Vedant Computers products:', len(vc_items))
    if vc_items:
        h4 = vc_items[0].select_one('h4, .name')
        p = vc_items[0].select_one('.price')
        print('  Sample:', h4.text.strip() if h4 else 'No title', '|', p.text.strip() if p else 'No price')
except Exception as e:
    print('Vedant error:', e)

# 2. PrimeABGB
try:
    r_p = s.get('https://www.primeabgb.com/buy-online-price-india/laptops/', timeout=15)
    soup_p = BeautifulSoup(r_p.text, 'lxml')
    p_items = soup_p.select('li.product, div.product')
    print('PrimeABGB products:', len(p_items))
    if p_items:
        t = p_items[0].select_one('.product-title, h3')
        p = p_items[0].select_one('.price')
        print('  Sample:', t.text.strip() if t else 'No title', '|', p.text.strip() if p else 'No price')
except Exception as e:
    print('PrimeABGB error:', e)

# 3. ShopClues
try:
    r_sc = s.get('https://www.shopclues.com/search?q=laptop&z=0', timeout=15)
    soup_sc = BeautifulSoup(r_sc.text, 'lxml')
    sc_items = soup_sc.select('.column.col3, .grid_show, div.search_blocks')
    print('ShopClues products:', len(sc_items))
    if sc_items:
        t = sc_items[0].select_one('h2, h3, .prod_name')
        p = sc_items[0].select_one('.p_price, .price')
        print('  Sample:', t.text.strip() if t else 'No title', '|', p.text.strip() if p else 'No price')
except Exception as e:
    print('ShopClues error:', e)
