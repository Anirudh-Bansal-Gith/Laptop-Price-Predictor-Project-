import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}
s = requests.Session()
s.headers.update(headers)

r = s.get('https://www.flipkart.com/search?q=laptop&page=1', timeout=15)
soup = BeautifulSoup(r.text, 'lxml')
cards = soup.select('div[data-id]')
print(f"Cards found on Flipkart: {len(cards)}")

for i, card in enumerate(cards[:5]):
    # Get title
    title_el = card.select_one('div.KzDlHZ, div._4rR01T, a[title]')
    title = title_el.text.strip() if title_el else ''
    if not title:
        # fallback to link or text
        link_el = card.select_one('a[href*="/p/"]')
        title = link_el.get('title', '') if link_el else ''
        if not title and link_el:
            img = link_el.select_one('img')
            title = img.get('alt', '') if img else ''
    
    # Get price
    price_el = card.select_one('div.Nx9bqj, div._30jeq3')
    price_text = price_el.text.strip() if price_el else ''
    
    # Get bullets
    bullets = [li.text.strip() for li in card.select('ul.G4BRas li, ul._1xgFaf li, li')]
    
    # Get URL
    link = card.select_one('a[href*="/p/"]')
    href = link.get('href', '') if link else ''
    if href.startswith('/'):
        href = 'https://www.flipkart.com' + href
    href = href.split('?')[0]
    
    print(f"\n--- Card {i+1} ---")
    print(f"Title: {title[:75]}")
    print(f"Price: {price_text.encode('ascii', 'replace').decode()}")
    print(f"Bullets ({len(bullets)}): {bullets[:5]}")
    print(f"URL: {href[:60]}")
