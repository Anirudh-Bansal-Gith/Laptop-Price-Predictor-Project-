from curl_cffi import requests
from bs4 import BeautifulSoup
import re

r = requests.get('https://www.reliancedigital.in/laptops/c/S101411', impersonate='chrome124')
soup = BeautifulSoup(r.text, 'lxml')
for s in soup.find_all('script'):
    if s.string and len(s.string) > 100000:
        print('Found large script len:', len(s.string))
        print('Prefix:', s.string[:200])
        # Find product names
        matches = re.findall(r'"name":"([^"]*laptop[^"]*)"', s.string, re.IGNORECASE)
        print('Laptops in script:', len(matches))
        for m in matches[:5]:
            print('  Product:', m)
