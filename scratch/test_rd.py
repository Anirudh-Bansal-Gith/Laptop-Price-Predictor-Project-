from curl_cffi import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.reliancedigital.in/',
}

url = 'https://www.reliancedigital.in/rildigitalws/v2/rrpl/products/search?q=laptop:relevance&page=0&size=24'
r = requests.get(url, headers=headers, impersonate='chrome124')
print('Reliance Digital API status:', r.status_code, 'Content-type:', r.headers.get('content-type'))
try:
    data = r.json()
    print('JSON keys:', list(data.keys()))
    print('Total results:', data.get('pagination', {}).get('totalResults'))
    print('First product:', data.get('products', [{}])[0].get('name'))
except Exception as e:
    print('Not JSON:', e, r.text[:200])
