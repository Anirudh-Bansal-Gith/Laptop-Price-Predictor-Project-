from curl_cffi import requests
from bs4 import BeautifulSoup
import json

url = 'https://www.croma.com/searchB?q=laptop%3Arelevance&text=laptop'
r = requests.get(url, impersonate='chrome124', timeout=15)
soup = BeautifulSoup(r.text, 'lxml')

for s in soup.find_all('script'):
    if s.string and 'window.__INITIAL_DATA__' in s.string:
        raw_json = s.string.split('window.__INITIAL_DATA__=')[1].strip()
        if raw_json.endswith(';'):
            raw_json = raw_json[:-1]
        data = json.loads(raw_json)
        print("Root keys:", list(data.keys()))
        # Let's inspect where products are
        for k, v in data.items():
            if isinstance(v, dict):
                print(f"  {k} subkeys:", list(v.keys())[:10])
                if 'products' in v or 'product' in str(v.keys()).lower():
                    print(f"    --> Found in {k}!")
