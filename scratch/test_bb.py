from curl_cffi import requests
from bs4 import BeautifulSoup

url = 'https://www.bestbuy.com/site/laptop-computers/all-laptops/pcmcat138500050001.c'
r = requests.get(url, impersonate='chrome124', timeout=15)
print('BestBuy status:', r.status_code, 'len:', len(r.text))
soup = BeautifulSoup(r.text, 'lxml')
print('Title:', soup.title.text if soup.title else 'None')
items = soup.select('li.sku-item, div.shop-sku-list-item, div.sku-item')
print('Product items found:', len(items))
if not items:
    # check any product links
    links = [a['href'] for a in soup.find_all('a', href=True) if '.p?skuId=' in a['href']]
    print('Product links with skuId:', len(links))
    if links:
        print('Sample link:', links[0])
