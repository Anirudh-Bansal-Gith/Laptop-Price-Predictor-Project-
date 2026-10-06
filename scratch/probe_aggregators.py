import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}
s = requests.Session()
s.headers.update(headers)

test_urls = [
    ('ShopClues', 'https://www.shopclues.com/search?q=laptop&z=0'),
    ('91mobiles', 'https://www.91mobiles.com/laptop-finder.php'),
    ('Smartprix', 'https://www.smartprix.com/laptops'),
    ('Pricebaba', 'https://pricebaba.com/laptops/pricelist/all-laptops-sold-in-india'),
    ('Digit', 'https://www.digit.in/laptops/'),
]

for name, url in test_urls:
    try:
        r = s.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        title = soup.title.text.strip() if soup.title else 'No title'
        print(f'{name:15s} | Status: {r.status_code} | Len: {len(r.text):8d} | Title: {title[:40]}')
    except Exception as e:
        print(f'{name:15s} | Error: {e}')
