import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}
soup = BeautifulSoup(requests.get('https://www.amazon.in/s?k=laptop', headers=headers).text, 'lxml')
cards = soup.select('div[data-component-type="s-search-result"]')
print('Amazon cards:', len(cards))
for c in cards[:3]:
    h2 = c.select_one('h2')
    p = c.select_one('span.a-price-whole')
    asin = c.get('data-asin')
    link = c.select_one('h2 a')
    href = 'https://www.amazon.in' + link['href'].split('/ref=')[0] if link and 'href' in link.attrs else ''
    print('-----------------------')
    print('ASIN:', asin, '| Price:', p.text.strip() if p else 'N/A')
    print('Title:', h2.text.strip()[:80] if h2 else 'N/A')
    print('Link:', href[:60])
