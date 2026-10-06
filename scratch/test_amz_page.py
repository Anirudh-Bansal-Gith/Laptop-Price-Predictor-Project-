import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}
s = requests.Session()
s.headers.update(headers)
r1 = s.get('https://www.amazon.in/s?k=laptop&page=1', timeout=15)
r2 = s.get('https://www.amazon.in/s?k=laptop&page=2', timeout=15)
soup1 = BeautifulSoup(r1.text, 'lxml')
soup2 = BeautifulSoup(r2.text, 'lxml')
c1 = soup1.select('div[data-component-type="s-search-result"]')
c2 = soup2.select('div[data-component-type="s-search-result"]')
print('Amz Page 1 items:', len(c1), 'first ASIN:', c1[0].get('data-asin') if c1 else 'None')
print('Amz Page 2 items:', len(c2), 'first ASIN:', c2[0].get('data-asin') if c2 else 'None')
