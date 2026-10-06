"""Web scraping module for laptop data collection.

Collects laptop specifications from multiple e-commerce platforms:
- Flipkart (flipkart.com)
- Amazon (amazon.in / amazon.com)
- Smartprix (smartprix.com)
- Best Buy (bestbuy.com)

Each scraper extracts 20+ features per laptop including granular CPU/GPU
generation and model details for price prediction modeling.
"""

from .base import BaseScraper
from .amazon_scraper import AmazonScraper
from .flipkart_scraper import FlipkartScraper
from .smartprix_scraper import SmartprixScraper
from .bestbuy_scraper import BestBuyScraper

__all__ = [
    "BaseScraper",
    "AmazonScraper",
    "FlipkartScraper",
    "SmartprixScraper",
    "BestBuyScraper",
]
