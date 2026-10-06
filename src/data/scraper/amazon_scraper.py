"""Amazon laptop scraper.

Scrapes laptop listings from Amazon.com search results and individual
product pages to extract 20+ hardware specification features.

Strategy:
    1. Search for 'laptops' across multiple category pages.
    2. Collect product listing URLs from search results.
    3. Visit each product page to extract detailed specifications.
    4. Parse CPU/GPU/Storage/RAM specs using base class utilities.
"""

import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from .base import BaseScraper

logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    """Scraper for Amazon laptop listings."""

    BASE_URL = "https://www.amazon.in"
    SEARCH_URL = f"{BASE_URL}/s"

    # Multiple search queries to maximize coverage and diversity
    SEARCH_QUERIES = [
        "laptop",
        "gaming laptop",
        "intel i5 laptop",
        "intel i7 laptop",
        "intel core ultra laptop",
        "amd ryzen laptop",
        "ryzen 7 laptop",
        "asus tuf laptop",
        "hp pavilion laptop",
        "hp victus laptop",
        "lenovo ideapad laptop",
        "dell inspiron laptop",
        "acer aspire laptop",
        "macbook air",
        "msi thin laptop",
        "rtx 4050 laptop",
        "rtx 3050 laptop",
        "ultrabook laptop",
        "oled laptop",
        "touchscreen laptop",
        "business laptop",
    ]

    def __init__(self, base_url: str = "https://www.amazon.in", **kwargs):
        super().__init__(platform="Amazon", min_delay=0.4, max_delay=1.0, **kwargs)
        self.BASE_URL = base_url
        self.SEARCH_URL = f"{base_url}/s"
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": f"{self.BASE_URL}/",
        })

    def _get_search_params(self, query: str, page: int) -> Dict[str, str]:
        """Build Amazon search query parameters."""
        return {
            "k": query,
            "page": str(page),
            "ref": f"sr_pg_{page}",
        }

    def _extract_product_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract product page URLs from a search results page."""
        links = []

        # Primary selectors for product cards
        selectors = [
            "div[data-component-type='s-search-result'] h2 a",
            "div.s-result-item h2 a.a-link-normal",
            "div.sg-col-inner h2 a",
            ".s-main-slot div[data-asin] h2 a",
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for el in elements:
                    href = el.get("href", "")
                    if href and "/dp/" in href:
                        if href.startswith("/"):
                            href = self.BASE_URL + href
                        # Clean tracking parameters
                        href = href.split("/ref=")[0]
                        if href not in links:
                            links.append(href)
                break  # Use first selector that works

        logger.info(f"[Amazon] Found {len(links)} product links on page")
        return links

    def _extract_spec_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract specifications from product detail tables."""
        specs = {}

        # Method 1: Product information table (most common)
        tables = soup.select("table.a-keyvalue.prodDetTable, table.a-bordered")
        for table in tables:
            rows = table.select("tr")
            for row in rows:
                header = row.select_one("th, td.a-span3")
                value = row.select_one("td.a-span9, td:last-child")
                if header and value:
                    key = header.get_text(strip=True).lower()
                    val = value.get_text(strip=True)
                    specs[key] = val

        # Method 2: Technical details section
        tech_section = soup.select_one("#productDetails_techSpec_section_1")
        if tech_section:
            rows = tech_section.select("tr")
            for row in rows:
                header = row.select_one("th")
                value = row.select_one("td")
                if header and value:
                    specs[header.get_text(strip=True).lower()] = value.get_text(strip=True)

        # Method 3: Feature bullets
        bullets = soup.select("#feature-bullets li span.a-list-item")
        for bullet in bullets:
            text = bullet.get_text(strip=True)
            specs[f"bullet_{len(specs)}"] = text

        # Method 4: Glance icon rows (newer Amazon layout)
        glance_rows = soup.select("#glance_icons_div tr, table.a-normal tr")
        for row in glance_rows:
            cells = row.select("td")
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).lower()
                val = cells[1].get_text(strip=True)
                if key and val:
                    specs[key] = val

        return specs

    def _parse_product_page(self, url: str) -> Optional[Dict[str, str]]:
        """Parse a single Amazon product page into a standardized row."""
        soup = self.fetch_page(url)
        if not soup:
            return None

        row = self.empty_row()
        row["source"] = "Amazon"
        row["url"] = url

        # ── Title and Brand ──
        title_el = soup.select_one("#productTitle, span#productTitle")
        title = title_el.get_text(strip=True) if title_el else ""
        row["model_name"] = title

        brand_el = soup.select_one("#bylineInfo, a#bylineInfo")
        if brand_el:
            brand_text = brand_el.get_text(strip=True)
            brand_text = re.sub(r"^(Visit the|Brand:)\s*", "", brand_text)
            brand_text = re.sub(r"\s*Store$", "", brand_text)
            row["brand"] = brand_text
        elif title:
            # Extract brand from title (first word usually)
            row["brand"] = title.split()[0] if title else ""

        # ── Price ──
        price_selectors = [
            "span.a-price span.a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "span.a-price-whole",
            ".a-price .a-offscreen",
        ]
        for sel in price_selectors:
            price_el = soup.select_one(sel)
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_val, currency = self.parse_price(price_text)
                if price_val:
                    row["price_original"] = price_val
                    row["price_usd"] = price_val
                    row["currency"] = "USD"
                    break

        # ── Specifications Table ──
        specs = self._extract_spec_table(soup)
        all_specs_text = " ".join(specs.values()).lower()

        # Map spec keys to our columns
        spec_mappings = {
            "screen_size_inches": ["screen size", "display size", "standing screen display size"],
            "screen_resolution": ["resolution", "screen resolution", "display resolution", "max display resolution"],
            "display_type": ["display type", "panel type", "display technology"],
            "cpu_raw": ["processor", "processor type", "cpu", "cpu model", "processor brand"],
            "ram_raw": ["ram", "memory", "system memory", "ram memory installed size", "ram size"],
            "storage_raw": ["hard drive", "storage", "hard disk size", "hard disk", "flash memory size", "hard drive size"],
            "gpu_raw": ["graphics", "gpu", "graphics coprocessor", "graphics card", "graphics card description", "chipset brand"],
            "operating_system": ["operating system", "os", "platform"],
            "weight_raw": ["weight", "item weight"],
            "battery_whr": ["battery", "batteries", "battery life", "watt hours", "wattage"],
        }

        for target, keys in spec_mappings.items():
            for key in keys:
                for spec_key, spec_val in specs.items():
                    if key in spec_key:
                        if target == "cpu_raw":
                            cpu_info = self.parse_cpu_string(spec_val)
                            row["cpu_brand"] = cpu_info["cpu_brand"]
                            row["cpu_family"] = cpu_info["cpu_family"]
                            row["cpu_model"] = cpu_info["cpu_model"]
                            row["cpu_generation"] = cpu_info["cpu_generation"]
                            row["cpu_base_clock_ghz"] = cpu_info["cpu_base_clock_ghz"]
                        elif target == "gpu_raw":
                            gpu_info = self.parse_gpu_string(spec_val)
                            row["gpu_brand"] = gpu_info["gpu_brand"]
                            row["gpu_model"] = gpu_info["gpu_model"]
                            row["gpu_vram_gb"] = gpu_info["gpu_vram_gb"]
                            row["gpu_generation"] = gpu_info["gpu_generation"]
                        elif target == "ram_raw":
                            ram_gb, ram_type = self.parse_ram(spec_val)
                            row["ram_gb"] = ram_gb
                            row["ram_type"] = ram_type
                        elif target == "storage_raw":
                            cap, stype, sec = self.parse_storage(spec_val)
                            row["storage_capacity_gb"] = cap
                            row["storage_type"] = stype
                            row["secondary_storage_gb"] = sec
                        elif target == "weight_raw":
                            row["weight_kg"] = self.parse_weight(spec_val)
                        elif target == "screen_size_inches":
                            size_match = re.search(r"(\d+\.?\d*)\s*(?:inches|in|\")", spec_val, re.IGNORECASE)
                            if size_match:
                                row["screen_size_inches"] = size_match.group(1)
                            else:
                                row["screen_size_inches"] = spec_val
                        elif target == "battery_whr":
                            whr_match = re.search(r"(\d+\.?\d*)\s*(?:Wh|watt)", spec_val, re.IGNORECASE)
                            if whr_match:
                                row["battery_whr"] = whr_match.group(1)
                        else:
                            row[target] = spec_val
                        break
                if row.get(target) or (target.endswith("_raw")):
                    break

        # ── Type classification from title ──
        title_lower = title.lower()
        if "gaming" in title_lower:
            row["type_name"] = "Gaming"
        elif "2-in-1" in title_lower or "2 in 1" in title_lower or "convertible" in title_lower:
            row["type_name"] = "2-in-1"
        elif "ultrabook" in title_lower or "ultra" in title_lower:
            row["type_name"] = "Ultrabook"
        elif "chromebook" in title_lower:
            row["type_name"] = "Chromebook"
        elif "workstation" in title_lower:
            row["type_name"] = "Workstation"
        elif "business" in title_lower:
            row["type_name"] = "Business"
        else:
            row["type_name"] = "Notebook"

        # ── Touchscreen detection ──
        if "touchscreen" in title_lower or "touch screen" in title_lower or "touchscreen" in all_specs_text:
            row["is_touchscreen"] = "1"
        else:
            row["is_touchscreen"] = "0"

        # ── Refresh rate ──
        refresh_match = re.search(r"(\d+)\s*Hz", title + " " + " ".join(specs.values()))
        if refresh_match:
            hz = int(refresh_match.group(1))
            if hz in (60, 90, 120, 144, 165, 240, 300, 360):
                row["refresh_rate_hz"] = str(hz)

        # ── CPU cores from specs ──
        cores_match = re.search(r"(\d+)\s*(?:-?\s*core|cores)", " ".join(specs.values()), re.IGNORECASE)
        if cores_match:
            row["cpu_cores"] = cores_match.group(1)

        # Validate: skip rows with too little data
        filled = sum(1 for v in row.values() if v and v not in ("", "0"))
        if filled < 8:
            logger.debug(f"[Amazon] Skipping product with only {filled} fields: {url}")
            return None

        return row

    def _parse_card(self, card) -> Optional[Dict[str, str]]:
        """Parse an Amazon search result card directly for specifications."""
        h2 = card.select_one("h2")
        if not h2:
            return None
        title = h2.text.strip()
        if not title:
            return None

        price_el = card.select_one("span.a-price-whole")
        if not price_el:
            return None
        price_clean = re.sub(r"[^\d]", "", price_el.text.strip())
        if not price_clean:
            return None

        asin = card.get("data-asin", "")
        link = card.select_one("h2 a")
        if link and link.get("href"):
            h = link["href"]
            url = (self.BASE_URL + h if h.startswith("/") else h).split("/ref=")[0]
        elif asin:
            url = f"{self.BASE_URL}/dp/{asin}"
        else:
            url = ""

        row = self.empty_row()
        row["source"] = "Amazon"
        row["model_name"] = title
        row["url"] = url
        row["price_original"] = price_clean
        row["currency"] = "INR" if "amazon.in" in self.BASE_URL else "USD"
        try:
            if row["currency"] == "INR":
                row["price_usd"] = f"{float(price_clean) * 0.012:.2f}"
            else:
                row["price_usd"] = f"{float(price_clean):.2f}"
        except ValueError:
            pass

        self.parse_title_features(title, row)
        return row

    def scrape(self, max_products: int = 400) -> List[Dict[str, str]]:
        """Scrape laptop data from Amazon search results.

        Args:
            max_products: Maximum number of laptops to collect.

        Returns:
            List of row dicts with 20+ features per laptop.
        """
        results = []
        seen_keys = set()

        logger.info(f"[Amazon] Starting scrape for up to {max_products} products")

        for query in self.SEARCH_QUERIES:
            if len(results) >= max_products:
                break

            for page in range(1, 15):
                if len(results) >= max_products:
                    break

                logger.info(f"[Amazon] Searching '{query}' page {page} ({len(results)}/{max_products} collected)")
                params = self._get_search_params(query, page)
                soup = self.fetch_page(self.SEARCH_URL, params=params)

                if not soup:
                    break

                cards = soup.select("div[data-component-type='s-search-result']")
                if not cards:
                    break

                page_new = 0
                for card in cards:
                    if len(results) >= max_products:
                        break
                    try:
                        row = self._parse_card(card)
                        if not row or not row.get("price_original"):
                            continue

                        key = row.get("url") or row.get("model_name", "")[:60]
                        if key not in seen_keys:
                            seen_keys.add(key)
                            results.append(row)
                            page_new += 1
                    except Exception as e:
                        logger.debug(f"[Amazon] Error parsing card: {e}")
                        continue

                logger.info(f"[Amazon] Added {page_new} laptops from '{query}' page {page}")
                if page_new == 0:
                    break

        logger.info(f"[Amazon] Successfully scraped {len(results)} laptops")
        return results
