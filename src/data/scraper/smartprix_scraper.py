"""Smartprix laptop scraper.

Scrapes rich laptop specification listings from Smartprix.com.
Provides granular specifications including CPU model, cores, threads,
RAM capacity, RAM technology, storage capacity, dedicated/integrated GPU model,
GPU generation, display size, and resolution.
"""

import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)

INR_TO_USD = 0.012


class SmartprixScraper(BaseScraper):
    """Scraper for Smartprix.com laptop catalog."""

    BASE_URL = "https://www.smartprix.com"

    CATEGORY_URLS = [
        "/laptops",
        "/laptops/lenovo-brand",
        "/laptops/asus-brand",
        "/laptops/hp-brand",
        "/laptops/dell-brand",
        "/laptops/acer-brand",
        "/laptops/apple-brand",
        "/laptops/msi-brand",
        "/laptops/samsung-brand",
        "/laptops/xiaomi-brand",
        "/laptops/infinix-brand",
        "/laptops/microsoft-brand",
        "/laptops/lg-brand",
        "/laptops/honor-brand",
        "/laptops/gaming-laptops",
        "/laptops/thin-and-light-laptops",
        "/laptops/oled-display-laptops",
        "/laptops/touch-screen-laptops",
        "/laptops/price-below_30000",
        "/laptops/price-30000_to_40000",
        "/laptops/price-40000_to_50000",
        "/laptops/price-50000_to_60000",
        "/laptops/price-60000_to_70000",
        "/laptops/price-70000_to_80000",
        "/laptops/price-80000_to_100000",
        "/laptops/price-above_100000",
    ]

    def __init__(self, **kwargs):
        super().__init__(platform="Smartprix", min_delay=0.4, max_delay=1.0, **kwargs)
        self.session.headers.update({
            "Referer": "https://www.smartprix.com/",
        })

    def _parse_card(self, card) -> Optional[Dict[str, str]]:
        """Parse a Smartprix laptop product card into a structured dictionary."""
        name_el = card.select_one("h2, .name, a[title]")
        if not name_el:
            return None
        title = name_el.text.strip()
        if not title:
            return None

        price_el = card.select_one(".price")
        if not price_el:
            return None
        price_clean = re.sub(r"[^\d]", "", price_el.text.strip())
        if not price_clean:
            return None

        link_el = card.select_one("a[href*='/laptops/']")
        href = ""
        if link_el and link_el.get("href"):
            h = link_el["href"]
            href = self.BASE_URL + h if h.startswith("/") else h

        features = [li.text.strip() for li in card.select("ul.features li, ul li")]

        row = self.empty_row()
        row["source"] = "Smartprix"
        row["model_name"] = title
        row["url"] = href
        row["price_original"] = price_clean
        row["currency"] = "INR"
        try:
            row["price_usd"] = f"{float(price_clean) * INR_TO_USD:.2f}"
        except ValueError:
            pass

        for feat in features:
            f_low = feat.lower()

            # CPU info
            if any(k in f_low for k in ["core", "ryzen", "snapdragon", "intel", "amd", "m1", "m2", "m3", "m4", "processor"]) and not any(k in f_low for k in ["rtx", "gtx", "geforce", "radeon"]):
                if not any(k in f_low for k in ["core,", "cores"]):
                    cpu_d = self.parse_cpu_string(feat)
                    for k, v in cpu_d.items():
                        if v and not row[k]:
                            row[k] = v

            # CPU Cores
            if "cores" in f_low or "core," in f_low:
                c_m = re.search(r"(\d+)\s*Cores?", feat, re.IGNORECASE)
                if c_m:
                    row["cpu_cores"] = c_m.group(1)
                elif "octa core" in f_low:
                    row["cpu_cores"] = "8"
                elif "hexa core" in f_low:
                    row["cpu_cores"] = "6"
                elif "quad core" in f_low:
                    row["cpu_cores"] = "4"
                elif "dual core" in f_low:
                    row["cpu_cores"] = "2"

            # RAM info
            if "ram" in f_low:
                r_gb, r_type = self.parse_ram(feat)
                if r_gb:
                    row["ram_gb"] = r_gb
                if r_type:
                    row["ram_type"] = r_type

            # Storage info
            if any(k in f_low for k in ["ssd", "hdd", "emmc"]):
                cap, stype, sec = self.parse_storage(feat)
                if cap:
                    row["storage_capacity_gb"] = cap
                if stype:
                    row["storage_type"] = stype
                if sec:
                    row["secondary_storage_gb"] = sec

            # GPU info
            if any(k in f_low for k in ["rtx", "gtx", "geforce", "radeon", "iris", "uhd", "graphics", "arc"]):
                gpu_d = self.parse_gpu_string(feat)
                for k, v in gpu_d.items():
                    if v:
                        row[k] = v

            # Display info
            if "inches" in f_low or "pixels" in f_low or "resolution" in f_low:
                sz_m = re.search(r"(\d{1,2}(?:\.\d{1,2})?)\s*inches?", feat, re.IGNORECASE)
                if sz_m:
                    row["screen_size_inches"] = sz_m.group(1)
                res_m = re.search(r"(\d{3,4}\s*[xX*×]\s*\d{3,4})", feat)
                if res_m:
                    row["screen_resolution"] = re.sub(r"\s*", "", res_m.group(1)).replace("X", "x")

        # Fill remaining features from title and features list
        combined = f"{title} {' '.join(features)}"
        self.parse_title_features(combined, row)
        return row

    def scrape(self, max_products: int = 400) -> List[Dict[str, str]]:
        """Scrape laptop data from Smartprix.

        Args:
            max_products: Maximum number of laptops to collect.

        Returns:
            List of row dicts with 20+ features per laptop.
        """
        results = []
        seen_keys = set()

        logger.info(f"[Smartprix] Starting scrape for up to {max_products} products")

        for cat_url in self.CATEGORY_URLS:
            if len(results) >= max_products:
                break

            target_url = self.BASE_URL + cat_url
            logger.info(f"[Smartprix] Scraping category '{cat_url}' ({len(results)}/{max_products} collected)")
            soup = self.fetch_page(target_url)

            if not soup:
                continue

            cards = soup.select("div.sm-product")
            if not cards:
                continue

            added = 0
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
                        added += 1
                except Exception as e:
                    logger.debug(f"[Smartprix] Error parsing card: {e}")
                    continue

            logger.info(f"[Smartprix] Added {added} laptops from '{cat_url}'")

        logger.info(f"[Smartprix] Successfully scraped {len(results)} laptops")
        return results
