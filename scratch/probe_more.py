import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}
s = requests.Session()
s.headers.update(headers)

test_urls = [
    ('Vijay Sales', 'https://www.vijaysales.com/search/laptop'),
    ('Reliance Digital', 'https://www.reliancedigital.in/laptops/c/S101411'),
    ('PCStudio', 'https://www.pcstudio.in/?s=laptop&post_type=product'),
    ('Computech', 'https://computechstore.in/?s=laptop&post_type=product'),
    ('EliteHubs', 'https://elitehubs.com/?s=laptop&post_type=product'),
    ('ITGadgets', 'https://itgadgets.in/?s=laptop&post_type=product'),
]

for name, url in test_urls:
    try:
        r = s.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        title = soup.title.text.strip() if soup.title else 'No title'
        print(f'{name:18s} | Status: {r.status_code} | Len: {len(r.text):8d} | Title: {title[:40]}')
    except Exception as e:
        print(f'{name:18s} | Error: {e}')
