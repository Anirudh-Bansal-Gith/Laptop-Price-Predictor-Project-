import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}

# 1. Test Amazon.in product cards
s = requests.Session()
s.headers.update(headers)
r_amz = s.get('https://www.amazon.in/s?k=laptop', timeout=15)
soup_amz = BeautifulSoup(r_amz.text, 'lxml')
amz_cards = soup_amz.select('div[data-component-type="s-search-result"]')
print(f"Amazon.in search cards: {len(amz_cards)}")
for card in amz_cards[:2]:
    h2 = card.select_one('h2')
    title = h2.text.strip() if h2 else 'No title'
    price = card.select_one('span.a-price-whole')
    price_val = price.text.strip() if price else 'No price'
    asin = card.get('data-asin', '')
    print(f"  ASIN: {asin} | Price: Rs.{price_val} | Title: {title[:70]}")

# 2. Test Flipkart search cards
r_fk = s.get('https://www.flipkart.com/search?q=laptop', timeout=15)
soup_fk = BeautifulSoup(r_fk.text, 'lxml')
fk_cards = soup_fk.select('div[data-id]')
print(f"\nFlipkart search cards: {len(fk_cards)}")
for card in fk_cards[:2]:
    # Extract title from text or link
    link = card.select_one('a[href*="/p/"]')
    text = card.get_text(separator=' | ')
    # find price
    price_m = re.search(r'₹([\d,]+)', text)
    price_str = price_m.group(1) if price_m else 'No price'
    title_m = re.search(r'Add to Compare \| (.*?)(?: \| \d\.\d)? \|', text)
    title_str = title_m.group(1) if title_m else text[:60]
    print(f"  Price: Rs.{price_str} | Title: {title_str[:70]}")

# 3. Test MD Computers
r_md = s.get('https://mdcomputers.in/index.php?route=product/search&search=laptop', timeout=15)
soup_md = BeautifulSoup(r_md.text, 'lxml')
md_cards = soup_md.select('.product-item-container, .product-layout')
print(f"\nMD Computers search cards: {len(md_cards)}")
for card in md_cards[:2]:
    title_el = card.select_one('.title-product, h4 a')
    title = title_el.text.strip() if title_el else 'No title'
    price_el = card.select_one('.price-new, .price')
    price = price_el.text.strip() if price_el else 'No price'
    print(f"  Price: {price} | Title: {title[:70]}")

# 4. Test Snapdeal
r_sd = s.get('https://www.snapdeal.com/search?keyword=laptop', timeout=15)
soup_sd = BeautifulSoup(r_sd.text, 'lxml')
sd_cards = soup_sd.select('.product-tuple-listing, .favDp')
print(f"\nSnapdeal search cards: {len(sd_cards)}")
for card in sd_cards[:2]:
    title_el = card.select_one('.product-title')
    title = title_el.text.strip() if title_el else 'No title'
    price_el = card.select_one('.product-price')
    price = price_el.text.strip() if price_el else 'No price'
    print(f"  Price: {price} | Title: {title[:70]}")
