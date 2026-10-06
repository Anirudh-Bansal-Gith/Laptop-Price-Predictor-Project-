"""Best Buy laptop scraper.

Scrapes laptop listings from BestBuy.com using their search/browse
pages and individual product specification pages.

Strategy:
    1. Browse laptop category and search pages.
    2. Collect product URLs from listing grids.
    3. Visit each product's "Specifications" tab for structured data.
    4. Parse all hardware specs into standardized columns.
"""

import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class BestBuyScraper(BaseScraper):
    """Scraper for BestBuy.com laptop listings."""

    BASE_URL = "https://www.bestbuy.com"

    # Category browsing URLs for laptops
    BROWSE_URLS = [
        "/site/laptop-computers/all-laptops/pcmcat138500050001.c",
        "/site/laptop-computers/all-laptops/pcmcat138500050001.c?qp=category_facet%3DGaming%20Laptops~pcmcat287600050003",
        "/site/laptop-computers/all-laptops/pcmcat138500050001.c?qp=category_facet%3D2%20in%201%20Laptops~pcmcat309300050009",
        "/site/laptop-computers/all-laptops/pcmcat138500050001.c?qp=category_facet%3DChromebooks~pcmcat244900050008",
    ]

    SEARCH_QUERIES = [
        "laptop",
        "gaming laptop",
        "ultrabook",
        "business laptop",
        "2 in 1 laptop",
        "macbook",
        "workstation laptop",
    ]

    def __init__(self, **kwargs):
        super().__init__(platform="BestBuy", min_delay=0.5, max_delay=1.5, timeout=10, **kwargs)
        self.session.headers.update({
            "Referer": "https://www.bestbuy.com/",
        })

    def _extract_product_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract product page URLs from Best Buy listing pages."""
        if soup.title and "international" in soup.title.text.lower():
            logger.warning("[BestBuy] Best Buy redirected to international gateway (geoblocked from current region).")
            return []

        links = []

        selectors = [
            "h4.sku-title a",
            "a.sku-header",
            "div.sku-item a.sku-title",
            "a[href*='/site/'][href*='.p']",
            "div.list-item a[href*='/site/']",
            "div.sku-item-list a",
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for el in elements:
                    href = el.get("href", "")
                    if href:
                        if href.startswith("/"):
                            href = self.BASE_URL + href
                        if "/site/" in href and (".p?" in href or href.endswith(".p")):
                            if href not in links:
                                links.append(href)
                if links:
                    break

        logger.info(f"[BestBuy] Found {len(links)} product links on page")
        return links

    def _extract_spec_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract specs from Best Buy product specification section."""
        specs = {}

        # Method 1: Specifications div (primary)
        spec_sections = soup.select("div.spec-categories div.row-title, div.spec-item")
        for item in spec_sections:
            label = item.select_one("div.row-title, span.row-title")
            value = item.select_one("div.row-value, span.row-value")
            if label and value:
                specs[label.get_text(strip=True).lower()] = value.get_text(strip=True)

        # Method 2: Key specs in overview section
        key_specs = soup.select("div.key-feature li, div.shop-specifications li")
        for li in key_specs:
            text = li.get_text(strip=True)
            specs[f"feature_{len(specs)}"] = text

        # Method 3: Shop specifications table
        shop_specs = soup.select("div.shop-product-spec div.spec-item, div.specification-item")
        for item in shop_specs:
            parts = item.select("div, span")
            if len(parts) >= 2:
                key = parts[0].get_text(strip=True).lower()
                val = parts[-1].get_text(strip=True)
                if key and val and key != val:
                    specs[key] = val

        # Method 4: Product attributes in JSON-LD
        scripts = soup.select("script[type='application/ld+json']")
        for script in scripts:
            try:
                import json
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    if "brand" in data:
                        brand = data["brand"]
                        if isinstance(brand, dict):
                            specs["brand_json"] = brand.get("name", "")
                        else:
                            specs["brand_json"] = str(brand)
                    for field in ["name", "description", "sku", "weight"]:
                        if field in data:
                            specs[f"json_{field}"] = str(data[field])
            except (json.JSONDecodeError, TypeError):
                continue

        return specs

    def _parse_product_page(self, url: str) -> Optional[Dict[str, str]]:
        """Parse a Best Buy product page into a standardized row."""
        soup = self.fetch_page(url)
        if not soup:
            return None

        row = self.empty_row()
        row["source"] = "BestBuy"
        row["url"] = url

        # ── Title ──
        title_el = soup.select_one(
            "h1.heading-5.v-fw-regular, "
            "div.sku-title h1, "
            "h1.shop-product-title"
        )
        title = title_el.get_text(strip=True) if title_el else ""
        row["model_name"] = title

        # ── Brand ──
        known_brands = [
            "HP", "Dell", "Lenovo", "ASUS", "Acer", "Apple", "MSI", "Samsung",
            "Microsoft", "LG", "Razer", "Alienware", "Google", "GIGABYTE",
            "Gateway", "Toshiba", "Dynabook",
        ]
        for brand in known_brands:
            if brand.lower() in title.lower():
                row["brand"] = brand
                break

        # ── Price ──
        price_selectors = [
            "div.priceView-hero-price span[aria-hidden='true']",
            "div.priceView-customer-price span",
            "div.pricing-price span.sr-only",
            "span.priceView-hero-price",
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

        # ── Specs ──
        specs = self._extract_spec_table(soup)
        all_text = " ".join(specs.values()).lower()

        # Brand from JSON-LD
        if not row["brand"] and "brand_json" in specs:
            row["brand"] = specs["brand_json"]

        # Map spec keys
        spec_mappings = {
            "cpu_raw": ["processor model", "processor", "processor type", "processor model number"],
            "cpu_brand_raw": ["processor brand"],
            "cpu_speed_raw": ["processor speed", "base clock speed", "processor speed (up to)"],
            "cpu_cores_raw": ["total number of processor cores", "number of processor cores"],
            "ram_raw": ["system memory (ram)", "system memory", "total installed ram"],
            "ram_type_raw": ["system memory ram type", "ram type", "type of memory (ram)"],
            "storage_raw": ["total storage capacity", "hard drive capacity", "solid state drive capacity"],
            "storage_type_raw": ["storage type"],
            "gpu_raw": ["graphics", "gpu brand", "gpu", "graphics type"],
            "gpu_vram_raw": ["gpu memory (ram)", "dedicated gpu memory"],
            "screen_size_raw": ["screen size", "display screen size", "screen size class"],
            "screen_res_raw": ["screen resolution", "display resolution", "native resolution"],
            "display_type_raw": ["display type", "screen type", "backlight technology"],
            "refresh_rate_raw": ["screen refresh rate", "refresh rate"],
            "touchscreen_raw": ["touchscreen", "touch screen"],
            "operating_system": ["operating system", "os name", "included os"],
            "weight_raw": ["product weight", "weight"],
            "battery_raw": ["battery life", "battery type", "battery capacity"],
            "type_raw": ["product type", "laptop type", "type"],
        }

        for target, keys in spec_mappings.items():
            for key in keys:
                for spec_key, spec_val in specs.items():
                    if key in spec_key:
                        self._map_bestbuy_spec(row, target, spec_val)
                        break
                # Check if we've already got data for this target
                relevant_field = {
                    "cpu_raw": "cpu_brand", "gpu_raw": "gpu_brand",
                    "ram_raw": "ram_gb", "storage_raw": "storage_capacity_gb",
                }
                if target in relevant_field and row.get(relevant_field[target]):
                    break

        # ── Type classification ──
        if not row["type_name"]:
            title_lower = title.lower()
            type_keywords = {
                "Gaming": ["gaming"],
                "2-in-1": ["2-in-1", "2 in 1", "convertible"],
                "Ultrabook": ["ultrabook"],
                "Chromebook": ["chromebook"],
                "Workstation": ["workstation"],
                "Business": ["business", "thinkpad"],
                "MacBook": ["macbook"],
            }
            for type_name, keywords in type_keywords.items():
                if any(kw in title_lower for kw in keywords):
                    row["type_name"] = type_name
                    break
            else:
                row["type_name"] = "Notebook"

        # Touchscreen detection
        if not row["is_touchscreen"]:
            if "touchscreen" in title.lower() or "yes" in specs.get("touchscreen", "").lower():
                row["is_touchscreen"] = "1"
            else:
                row["is_touchscreen"] = "0"

        # Validate
        filled = sum(1 for v in row.values() if v and v not in ("", "0"))
        if filled < 8:
            return None

        return row

    def _map_bestbuy_spec(self, row: Dict, target: str, value: str) -> None:
        """Map a Best Buy spec value to the standardized row."""
        if target == "cpu_raw":
            cpu_info = self.parse_cpu_string(value)
            row["cpu_brand"] = row["cpu_brand"] or cpu_info["cpu_brand"]
            row["cpu_family"] = row["cpu_family"] or cpu_info["cpu_family"]
            row["cpu_model"] = row["cpu_model"] or cpu_info["cpu_model"]
            row["cpu_generation"] = row["cpu_generation"] or cpu_info["cpu_generation"]
            row["cpu_base_clock_ghz"] = row["cpu_base_clock_ghz"] or cpu_info["cpu_base_clock_ghz"]
        elif target == "cpu_brand_raw":
            if not row["cpu_brand"]:
                row["cpu_brand"] = value
        elif target == "cpu_speed_raw":
            clock = re.search(r"(\d+\.?\d*)\s*GHz", value, re.IGNORECASE)
            if clock and not row["cpu_base_clock_ghz"]:
                row["cpu_base_clock_ghz"] = clock.group(1)
        elif target == "cpu_cores_raw":
            cores = re.search(r"(\d+)", value)
            if cores and not row["cpu_cores"]:
                row["cpu_cores"] = cores.group(1)
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
        elif target == "storage_type_raw":
            if not row["storage_type"]:
                row["storage_type"] = value.upper()
        elif target == "gpu_raw":
            gpu_info = self.parse_gpu_string(value)
            row["gpu_brand"] = row["gpu_brand"] or gpu_info["gpu_brand"]
            row["gpu_model"] = row["gpu_model"] or gpu_info["gpu_model"]
            row["gpu_vram_gb"] = row["gpu_vram_gb"] or gpu_info["gpu_vram_gb"]
            row["gpu_generation"] = row["gpu_generation"] or gpu_info["gpu_generation"]
        elif target == "gpu_vram_raw":
            vram = re.search(r"(\d+)\s*GB", value, re.IGNORECASE)
            if vram and not row["gpu_vram_gb"]:
                row["gpu_vram_gb"] = vram.group(1)
        elif target == "screen_size_raw":
            size = re.search(r"(\d+\.?\d*)", value)
            if size and not row["screen_size_inches"]:
                row["screen_size_inches"] = size.group(1)
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
            row["is_touchscreen"] = "1" if "yes" in value.lower() else "0"
        elif target == "operating_system":
            if not row["operating_system"]:
                row["operating_system"] = value
        elif target == "weight_raw":
            if not row["weight_kg"]:
                row["weight_kg"] = self.parse_weight(value)
        elif target == "battery_raw":
            whr = re.search(r"(\d+\.?\d*)\s*(?:Wh|watt)", value, re.IGNORECASE)
            if whr and not row["battery_whr"]:
                row["battery_whr"] = whr.group(1)
        elif target == "type_raw":
            if not row["type_name"]:
                row["type_name"] = value

    def scrape(self, max_products: int = 400) -> List[Dict[str, str]]:
        """Scrape laptop data from Best Buy.

        Args:
            max_products: Maximum number of laptops to collect.

        Returns:
            List of row dicts with 20+ features per laptop.
        """
        all_links = []
        seen_urls = set()

        logger.info(f"[BestBuy] Starting scrape for up to {max_products} products")

        # Method 1: Browse category pages
        for browse_url in self.BROWSE_URLS:
            if len(all_links) >= max_products * 2:
                break

            for page in range(1, 8):
                if len(all_links) >= max_products * 2:
                    break

                url = f"{self.BASE_URL}{browse_url}"
                if page > 1:
                    url += f"&cp={page}"

                logger.info(f"[BestBuy] Browsing category page {page}")
                soup = self.fetch_page(url)

                if not soup:
                    break

                links = self._extract_product_links(soup)
                if not links:
                    break

                for link in links:
                    if link not in seen_urls:
                        seen_urls.add(link)
                        all_links.append(link)

        # Method 2: Search queries
        for query in self.SEARCH_QUERIES:
            if len(all_links) >= max_products * 2:
                break

            for page in range(1, 6):
                if len(all_links) >= max_products * 2:
                    break

                search_url = f"{self.BASE_URL}/site/searchpage.jsp"
                params = {"st": query, "cp": str(page)}

                logger.info(f"[BestBuy] Searching '{query}' page {page}")
                soup = self.fetch_page(search_url, params=params)

                if not soup:
                    break

                links = self._extract_product_links(soup)
                if not links:
                    break

                for link in links:
                    if link not in seen_urls:
                        seen_urls.add(link)
                        all_links.append(link)

        logger.info(f"[BestBuy] Collected {len(all_links)} unique product links")

        results = []
        for i, link in enumerate(all_links):
            if len(results) >= max_products:
                break

            logger.info(f"[BestBuy] Processing product {i + 1}/{len(all_links)} ({len(results)} collected)")

            try:
                row = self._parse_product_page(link)
                if row:
                    results.append(row)
            except Exception as e:
                logger.error(f"[BestBuy] Error processing {link}: {e}")
                continue

        logger.info(f"[BestBuy] Successfully scraped {len(results)} laptops")
        return results
