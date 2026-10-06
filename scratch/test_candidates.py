from curl_cffi import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

candidates = [
    ('eBay', 'https://www.ebay.com/sch/i.html?_nkw=laptop&_sacat=175672'),
    ('Newegg', 'https://www.newegg.com/Laptops-Notebooks/SubCategory/ID-32'),
    ('Vijay Sales', 'https://www.vijaysales.com/laptops-tablets/laptops'),
    ('Computech', 'https://computechstore.in/product-category/laptops/'),
    ('Croma', 'https://www.croma.com/searchB?q=laptop%3Arelevance&text=laptop'),
]

for name, url in candidates:
    try:
        r = requests.get(url, impersonate='chrome124', timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        title = soup.title.text.strip() if soup.title else 'No title'
        print(f'{name:15s} | Status: {r.status_code} | Len: {len(r.text):7d} | Title: {title[:40]}')
    except Exception as e:
        print(f'{name:15s} | Error: {e}')
