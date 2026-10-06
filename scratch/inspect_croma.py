from curl_cffi import requests
from bs4 import BeautifulSoup

url = 'https://www.croma.com/searchB?q=laptop%3Arelevance&text=laptop'
r = requests.get(url, impersonate='chrome124', timeout=15)
print('Croma status:', r.status_code, 'Length:', len(r.text))
soup = BeautifulSoup(r.text, 'lxml')
# Look for scripts containing JSON data
for s in soup.find_all('script'):
    if s.string and ('product' in s.string.lower() or 'price' in s.string.lower()):
        print('Script found, len:', len(s.string), 'preview:', s.string[:100].strip())
