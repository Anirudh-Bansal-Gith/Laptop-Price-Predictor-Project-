import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-IN,en;q=0.9',
}

sites = [
    ('Amazon IN', 'https://www.amazon.in/s?k=laptop'),
    ('Amazon US', 'https://www.amazon.com/s?k=laptop'),
    ('Flipkart', 'https://www.flipkart.com/search?q=laptop'),
    ('Snapdeal', 'https://www.snapdeal.com/search?keyword=laptop'),
    ('MDComputers', 'https://mdcomputers.in/index.php?route=product/search&search=laptop'),
    ('PrimeABGB', 'https://www.primeabgb.com/?post_type=product&taxonomy=product_cat&s=laptop'),
    ('VedantComputers', 'https://www.vedantcomputers.com/index.php?route=product/search&search=laptop'),
]

for name, url in sites:
    try:
        s = requests.Session()
        s.headers.update(headers)
        r = s.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        title = soup.title.text.strip() if soup.title else 'No title'
        print(f'{name:18s} | Status: {r.status_code} | Len: {len(r.text):8d} | Title: {title[:45]}')
    except Exception as e:
        print(f'{name:18s} | Error: {e}')
