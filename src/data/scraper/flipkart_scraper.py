"""Flipkart laptop scraper.

Scrapes laptop listings from Flipkart.com search results and product
pages. Flipkart uses a mix of server-rendered HTML and structured
specification tables, making it amenable to BeautifulSoup parsing.

Strategy:
    1. Search for laptops across multiple category filters.
    2. Collect product listing URLs from paginated search results.
    3. Visit each product page and parse the structured spec table.
    4. Convert INR prices to USD using a fixed exchange rate.
"""

import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)

# Approximate INR to USD exchange rate
INR_TO_USD = 0.012


class FlipkartScraper(BaseScraper):
    """Scraper for Flipkart.com laptop listings."""

    BASE_URL = "https://www.flipkart.com"
    SEARCH_URL = f"{BASE_URL}/search"

    SEARCH_QUERIES = [
        "laptop",
        "gaming laptop",
        "hp laptop",
        "lenovo laptop",
        "asus laptop",
        "dell laptop",
        "acer laptop",
        "apple macbook",
        "msi laptop",
        "samsung galaxy book",
        "i5 laptop",
        "i7 laptop",
        "ryzen 5 laptop",
        "ryzen 7 laptop",
        "oled laptop",
        "rtx 3050 laptop",
        "rtx 4060 laptop",
        "thin light laptop",
        "touchscreen laptop",
    ]

    def __init__(self, **kwargs):
        super().__init__(platform="Flipkart", min_delay=0.4, max_delay=1.0, **kwargs)
        self.session.headers.update({
            "Referer": "https://www.flipkart.com/",
        })

    def _get_search_params(self, query: str, page: int) -> Dict[str, str]:
        """Build Flipkart search parameters."""
        return {
            "q": query,
            "otracker": "search",
            "otracker1": "search",
            "page": str(page),
        }

    def _extract_product_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract product page URLs from Flipkart search results."""
        links = []

        # Flipkart product card link selectors
        selectors = [
            "a.CGtC98",           # Common product card link class
            "a._1fQZEK",         # Alternate class
            "a.s1Q9rs",          # Another variant
            "a[href*='/p/']",    # Generic: any link pointing to a product page
            "div._1AtVbE a",     # Wrapper div
            "a.IRpwTa",          # Grid view
            "a._2rpwqI",         # List view
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for el in elements:
                    href = el.get("href", "")
                    if href and ("/p/" in href or "pid=" in href.lower()):
                        if href.startswith("/"):
                            href = self.BASE_URL + href
                        # Remove tracking params
                        href = href.split("&lid=")[0]
                        if href not in links:
                            links.append(href)
                if links:
                    break

        logger.info(f"[Flipkart] Found {len(links)} product links on page")
        return links

    def _extract_spec_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract specification key-value pairs from Flipkart product page."""
        specs = {}

        # Method 1: Structured spec table (most Flipkart product pages)
        spec_rows = soup.select("div._0ZhAN9, tr._1s_Smc, div.GNDEQ-")
        for row in spec_rows:
            cells = row.select("td, div")
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).lower()
                val = cells[-1].get_text(strip=True)
                if key and val and key != val:
                    specs[key] = val

        # Method 2: Key-value table rows
        table_rows = soup.select("table._14cfVK tr, div._3Rrcbo div.row")
        for row in table_rows:
            header = row.select_one("td:first-child, div:first-child")
            value = row.select_one("td:last-child, div:last-child")
            if header and value:
                key = header.get_text(strip=True).lower()
                val = value.get_text(strip=True)
                if key and val and key != val:
                    specs[key] = val

        # Method 3: Spec sections with headers
        sections = soup.select("div._3k-BhJ, div.X3BRps")
        for section in sections:
            rows = section.select("div._21lJbe, div.row")
            for row in rows:
                children = row.find_all(["div", "td", "span"], recursive=False)
                if len(children) >= 2:
                    key = children[0].get_text(strip=True).lower()
                    val = children[-1].get_text(strip=True)
                    if key and val and key != val:
                        specs[key] = val

        # Method 4: Highlights / key features
        highlights = soup.select("div._2418kt li, div.ZN3sAE li")
        for i, li in enumerate(highlights):
            text = li.get_text(strip=True)
            specs[f"highlight_{i}"] = text

        return specs

    def _parse_product_page(self, url: str) -> Optional[Dict[str, str]]:
        """Parse a Flipkart product page into a standardized row."""
        soup = self.fetch_page(url)
        if not soup:
            return None

        row = self.empty_row()
        row["source"] = "Flipkart"
        row["url"] = url

        # ── Title ──
        title_el = soup.select_one("span.VU-ZEz, h1.yhB1nd, span.B_NuCI")
        title = title_el.get_text(strip=True) if title_el else ""
        row["model_name"] = title

        # ── Brand extraction from title or breadcrumb ──
        known_brands = [
            "HP", "Dell", "Lenovo", "Asus", "Acer", "Apple", "MSI", "Samsung",
            "Microsoft", "LG", "Razer", "Huawei", "Honor", "Xiaomi", "Realme",
            "Infinix", "Avita", "Primebook", "Chuwi", "Ultimus", "Wings",
            "Thomson", "Nokia", "RedmiBook", "Zebronics", "AXL",
        ]
        for brand in known_brands:
            if brand.lower() in title.lower():
                row["brand"] = brand
                break

        if not row["brand"]:
            breadcrumb = soup.select_one("div._1MR4o5, div._3GIHBu")
            if breadcrumb:
                row["brand"] = breadcrumb.get_text(strip=True).split(">")[-2].strip() if ">" in breadcrumb.get_text() else ""

        # ── Price ──
        price_selectors = [
            "div.Nx9bqj.CxhGGd",  # Current price
            "div._30jeq3",          # Alternate price class
            "div.Nx9bqj",           # Price wrapper
            "div._16Jk6d",          # Deal price
        ]
        for sel in price_selectors:
            price_el = soup.select_one(sel)
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_val, currency = self.parse_price(price_text)
                if price_val:
                    row["price_original"] = price_val
                    row["currency"] = "INR"
                    try:
                        row["price_usd"] = f"{float(price_val) * INR_TO_USD:.2f}"
                    except (ValueError, TypeError):
                        row["price_usd"] = ""
                    break

        # ── Specification Table ──
        specs = self._extract_spec_table(soup)
        all_text = " ".join(specs.values()).lower()

        # Map Flipkart spec keys to our standardized columns
        spec_mappings = {
            "cpu_raw": ["processor name", "processor", "processor brand", "processor type", "cpu"],
            "cpu_generation_raw": ["processor generation", "generation"],
            "cpu_cores_raw": ["number of cores", "cores", "processor core"],
            "cpu_clock_raw": ["clock speed", "processor speed", "base clock"],
            "ram_raw": ["ram", "system memory", "ram type", "memory"],
            "ram_type_raw": ["ram type", "memory type"],
            "storage_raw": ["ssd", "hdd", "storage", "hard disk", "internal storage", "ssd capacity"],
            "gpu_raw": ["graphic processor", "graphics", "gpu", "dedicated graphic memory", "graphic card"],
            "screen_size_raw": ["screen size", "display size"],
            "screen_res_raw": ["screen resolution", "resolution", "display resolution"],
            "display_type_raw": ["display type", "screen type", "panel type"],
            "refresh_rate_raw": ["refresh rate"],
            "touchscreen_raw": ["touchscreen"],
            "operating_system": ["operating system", "os"],
            "weight_raw": ["weight"],
            "battery_raw": ["battery cell", "battery", "battery backup", "power supply"],
            "type_raw": ["type", "laptop type", "series"],
        }

        for target, keys in spec_mappings.items():
            for key in keys:
                for spec_key, spec_val in specs.items():
                    if key in spec_key:
                        self._map_flipkart_spec(row, target, spec_val)
                        break
                if target in ("cpu_raw",) and row.get("cpu_brand"):
                    break

        # ── Type classification ──
        if not row["type_name"]:
            title_lower = title.lower()
            if "gaming" in title_lower:
                row["type_name"] = "Gaming"
            elif "2-in-1" in title_lower or "2 in 1" in title_lower or "convertible" in title_lower:
                row["type_name"] = "2-in-1"
            elif "ultrabook" in title_lower or "ultra slim" in title_lower or "thin" in title_lower:
                row["type_name"] = "Ultrabook"
            elif "chromebook" in title_lower:
                row["type_name"] = "Chromebook"
            elif "workstation" in title_lower:
                row["type_name"] = "Workstation"
            elif "business" in title_lower:
                row["type_name"] = "Business"
            else:
                row["type_name"] = "Notebook"

        # ── Touchscreen from title ──
        if not row["is_touchscreen"]:
            if "touchscreen" in title.lower() or "touch" in all_text:
                row["is_touchscreen"] = "1"
            else:
                row["is_touchscreen"] = "0"

        # ── Refresh rate from highlights ──
        if not row["refresh_rate_hz"]:
            refresh_match = re.search(r"(\d+)\s*Hz", title + " " + " ".join(specs.values()))
            if refresh_match:
                hz = int(refresh_match.group(1))
                if hz in (60, 90, 120, 144, 165, 240, 300, 360):
                    row["refresh_rate_hz"] = str(hz)

        # Validate
        filled = sum(1 for v in row.values() if v and v not in ("", "0"))
        if filled < 8:
            logger.debug(f"[Flipkart] Skipping product with only {filled} fields: {url}")
            return None

        return row

    def _map_flipkart_spec(self, row: Dict, target: str, value: str) -> None:
        """Map a Flipkart spec value to the standardized row."""
        if target == "cpu_raw":
            cpu_info = self.parse_cpu_string(value)
            row["cpu_brand"] = row["cpu_brand"] or cpu_info["cpu_brand"]
            row["cpu_family"] = row["cpu_family"] or cpu_info["cpu_family"]
            row["cpu_model"] = row["cpu_model"] or cpu_info["cpu_model"]
            row["cpu_generation"] = row["cpu_generation"] or cpu_info["cpu_generation"]
            row["cpu_base_clock_ghz"] = row["cpu_base_clock_ghz"] or cpu_info["cpu_base_clock_ghz"]
        elif target == "cpu_generation_raw":
            if not row["cpu_generation"]:
                row["cpu_generation"] = value
        elif target == "cpu_cores_raw":
            cores = re.search(r"(\d+)", value)
            if cores:
                row["cpu_cores"] = cores.group(1)
        elif target == "cpu_clock_raw":
            clock = re.search(r"(\d+\.?\d*)\s*GHz", value, re.IGNORECASE)
            if clock and not row["cpu_base_clock_ghz"]:
                row["cpu_base_clock_ghz"] = clock.group(1)
        elif target == "ram_raw":
            ram_gb, ram_type = self.parse_ram(value)
            row["ram_gb"] = row["ram_gb"] or ram_gb
            row["ram_type"] = row["ram_type"] or ram_type
        elif target == "ram_type_raw":
            type_match = re.search(r"(DDR5|DDR4|DDR3|LPDDR5X|LPDDR5|LPDDR4X|LPDDR4)", value, re.IGNORECASE)
            if type_match and not row["ram_type"]:
                row["ram_type"] = type_match.group(1).upper()
        elif target == "storage_raw":
            cap, stype, sec = self.parse_storage(value)
            row["storage_capacity_gb"] = row["storage_capacity_gb"] or cap
            row["storage_type"] = row["storage_type"] or stype
            row["secondary_storage_gb"] = row["secondary_storage_gb"] or sec
        elif target == "gpu_raw":
            gpu_info = self.parse_gpu_string(value)
            row["gpu_brand"] = row["gpu_brand"] or gpu_info["gpu_brand"]
            row["gpu_model"] = row["gpu_model"] or gpu_info["gpu_model"]
            row["gpu_vram_gb"] = row["gpu_vram_gb"] or gpu_info["gpu_vram_gb"]
            row["gpu_generation"] = row["gpu_generation"] or gpu_info["gpu_generation"]
        elif target == "screen_size_raw":
            size = re.search(r"(\d+\.?\d*)\s*(?:inches|inch|in|cm|\")?", value, re.IGNORECASE)
            if size and not row["screen_size_inches"]:
                val = float(size.group(1))
                # Convert cm to inches if > 30
                if val > 30:
                    val = val / 2.54
                row["screen_size_inches"] = f"{val:.1f}"
        elif target == "screen_res_raw":
            if not row["screen_resolution"]:
                res = re.search(r"(\d{3,4})\s*x\s*(\d{3,4})", value)
                if res:
                    row["screen_resolution"] = f"{res.group(1)}x{res.group(2)}"
                else:
                    row["screen_resolution"] = value
        elif target == "display_type_raw":
            if not row["display_type"]:
                row["display_type"] = value
        elif target == "refresh_rate_raw":
            hz = re.search(r"(\d+)\s*Hz", value, re.IGNORECASE)
            if hz and not row["refresh_rate_hz"]:
                row["refresh_rate_hz"] = hz.group(1)
        elif target == "touchscreen_raw":
            if "yes" in value.lower():
                row["is_touchscreen"] = "1"
            else:
                row["is_touchscreen"] = "0"
        elif target == "operating_system":
            if not row["operating_system"]:
                row["operating_system"] = value
        elif target == "weight_raw":
            if not row["weight_kg"]:
                row["weight_kg"] = self.parse_weight(value)
        elif target == "battery_raw":
            whr = re.search(r"(\d+\.?\d*)\s*(?:Wh|watt\s*hour)", value, re.IGNORECASE)
            if whr and not row["battery_whr"]:
                row["battery_whr"] = whr.group(1)
        elif target == "type_raw":
            if not row["type_name"]:
                row["type_name"] = value

    def _parse_card(self, card) -> Optional[Dict[str, str]]:
        """Parse a Flipkart search result card directly for specifications."""
        # ── Title ──
        title = ""
        img = card.select_one("img[alt]")
        if img and img.get("alt"):
            title = img.get("alt").strip()
        if not title:
            title_el = card.select_one("div.KzDlHZ, div._4rR01T, a[title]")
            if title_el:
                title = title_el.text.strip()
        if not title:
            link_el = card.select_one("a[href*='/p/']")
            if link_el:
                title = link_el.get("title", "").strip()
        if not title:
            return None

        # ── Price ──
        card_text = card.get_text(separator=" | ")
        price_m = re.search(r"₹\s*([\d,]+)", card_text)
        if not price_m:
            return None
        price_inr = price_m.group(1).replace(",", "")

        # ── URL ──
        link = card.select_one("a[href*='/p/']")
        href = ""
        if link and link.get("href"):
            h = link["href"]
            href = (self.BASE_URL + h if h.startswith("/") else h).split("?")[0]

        row = self.empty_row()
        row["source"] = "Flipkart"
        row["model_name"] = title
        row["url"] = href
        row["price_original"] = price_inr
        row["currency"] = "INR"
        try:
            row["price_usd"] = f"{float(price_inr) * INR_TO_USD:.2f}"
        except ValueError:
            pass

        # ── Bullets ──
        bullets = [li.text.strip() for li in card.select("ul.G4BRas li, ul._1xgFaf li, li")]
        for b in bullets:
            b_low = b.lower()
            if any(k in b_low for k in ["processor", "core", "ryzen"]):
                cpu_d = self.parse_cpu_string(b)
                for k, v in cpu_d.items():
                    if v:
                        row[k] = v
            if "ram" in b_low:
                r_gb, r_type = self.parse_ram(b)
                if r_gb:
                    row["ram_gb"] = r_gb
                if r_type:
                    row["ram_type"] = r_type
            if any(k in b_low for k in ["ssd", "hdd", "emmc"]):
                cap, stype, sec = self.parse_storage(b)
                if cap:
                    row["storage_capacity_gb"] = cap
                if stype:
                    row["storage_type"] = stype
                if sec:
                    row["secondary_storage_gb"] = sec
            if any(k in b_low for k in ["display", "inch", "cm"]):
                sz_m = re.search(r"(\d{1,2}(?:\.\d{1,2})?)\s*(?:inch|cm\s*\(([\d.]+)\s*inch)", b, re.IGNORECASE)
                if sz_m:
                    row["screen_size_inches"] = sz_m.group(2) if sz_m.group(2) else sz_m.group(1)
            if any(k in b_low for k in ["operating system", "windows", "chrome"]):
                if "windows 11" in b_low:
                    row["operating_system"] = "Windows 11"
                elif "windows 10" in b_low:
                    row["operating_system"] = "Windows 10"
                elif "chrome" in b_low:
                    row["operating_system"] = "Chrome OS"

        # Combine title and bullets to fill any remaining fields
        combined = f"{title} {' '.join(bullets)}"
        self.parse_title_features(combined, row)
        return row

    def scrape(self, max_products: int = 400) -> List[Dict[str, str]]:
        """Scrape laptop data from Flipkart.

        Args:
            max_products: Maximum number of laptops to collect.

        Returns:
            List of row dicts with 20+ features per laptop.
        """
        results = []
        seen_keys = set()

        logger.info(f"[Flipkart] Starting scrape for up to {max_products} products")

        for query in self.SEARCH_QUERIES:
            if len(results) >= max_products:
                break

            for page in range(1, 15):
                if len(results) >= max_products:
                    break

                logger.info(f"[Flipkart] Searching '{query}' page {page} ({len(results)}/{max_products} collected)")
                params = self._get_search_params(query, page)
                soup = self.fetch_page(self.SEARCH_URL, params=params)

                if not soup:
                    break

                cards = soup.select("div[data-id]")
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

                        # Deduplicate by url or model fingerprint
                        key = row.get("url") or row.get("model_name", "")[:60]
                        if key not in seen_keys:
                            seen_keys.add(key)
                            results.append(row)
                            page_new += 1
                    except Exception as e:
                        logger.debug(f"[Flipkart] Error parsing card: {e}")
                        continue

                logger.info(f"[Flipkart] Added {page_new} laptops from '{query}' page {page}")
                if page_new == 0:
                    break

        logger.info(f"[Flipkart] Successfully scraped {len(results)} laptops")
        return results
