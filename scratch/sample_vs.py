import requests as req
from bs4 import BeautifulSoup

url_vs = 'https://www.vijaysales.com/search/laptop'
r_vs = req.get(url_vs, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=15)
soup_vs = BeautifulSoup(r_vs.text, 'lxml')
vs_links = [a['href'] for a in soup_vs.find_all('a', href=True) if '/p/' in a['href'] or '/product/' in a['href']]
print("First 10 Vijay Sales links:")
for l in vs_links[:10]:
    print(" ", l)
