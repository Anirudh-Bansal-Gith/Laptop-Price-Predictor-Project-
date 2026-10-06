"""Laptop data scraper orchestrator.

Runs all three e-commerce scrapers (Amazon, Flipkart, Best Buy),
merges the results, deduplicates, validates, and outputs a single
CSV file with 1000+ rows and 20+ columns per laptop.

Usage:
    python -m src.data.scraper.run_scraper
    python -m src.data.scraper.run_scraper --max-per-site 500 --output data/raw/scraped_laptops.csv
"""

import argparse
import hashlib
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd

# Add project root to path for imports
project_root = str(Path(__file__).resolve().parents[3])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set Windows console to UTF-8 to prevent charmap encoding errors
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.data.scraper.amazon_scraper import AmazonScraper
from src.data.scraper.bestbuy_scraper import BestBuyScraper
from src.data.scraper.flipkart_scraper import FlipkartScraper
from src.data.scraper.smartprix_scraper import SmartprixScraper
from src.data.scraper.base import BaseScraper


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging with timestamps and scraper source identification."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                Path(project_root) / "data" / "raw" / "scraper.log",
                mode="a",
                encoding="utf-8",
            ),
        ],
    )


def deduplicate_rows(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate laptops based on a content hash of key identifying fields.

    Args:
        data: List of scraped row dictionaries.

    Returns:
        Deduplicated list of rows.
    """
    seen_hashes = set()
    unique_rows = []

    for row in data:
        # Create a fingerprint from key identifying fields
        fingerprint_fields = [
            row.get("brand", "").lower().strip(),
            row.get("model_name", "").lower().strip()[:80],
            row.get("cpu_model", "").lower().strip(),
            row.get("ram_gb", "").strip(),
            row.get("storage_capacity_gb", "").strip(),
        ]
        fingerprint = "|".join(fingerprint_fields)
        content_hash = hashlib.md5(fingerprint.encode()).hexdigest()

        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_rows.append(row)

    removed = len(data) - len(unique_rows)
    if removed > 0:
        logging.getLogger(__name__).info(f"Deduplication removed {removed} duplicate rows")

    return unique_rows


def validate_and_clean(data: List[Dict[str, str]]) -> pd.DataFrame:
    """Validate scraped data quality and clean values.

    Args:
        data: List of scraped row dicts.

    Returns:
        Cleaned pandas DataFrame.
    """
    logger = logging.getLogger(__name__)
    df = pd.DataFrame(data, columns=BaseScraper.COLUMNS)

    initial_rows = len(df)

    # Fill missing values with empty strings
    df = df.fillna("")

    # Remove rows with no brand AND no model_name (totally empty)
    df = df[~((df["brand"] == "") & (df["model_name"] == ""))]

    # Remove rows with no price at all
    df = df[df["price_original"] != ""]

    # Standardize brand names
    brand_map = {
        "hewlett-packard": "HP",
        "hewlett packard": "HP",
        "hp inc.": "HP",
        "dell technologies": "Dell",
        "lenovo group": "Lenovo",
        "asustek": "ASUS",
        "asus": "ASUS",
        "acer inc.": "Acer",
        "acer america": "Acer",
        "micro-star international": "MSI",
        "microsoft corporation": "Microsoft",
        "lg electronics": "LG",
        "samsung electronics": "Samsung",
    }
    df["brand"] = df["brand"].apply(
        lambda x: brand_map.get(x.lower().strip(), x.strip())
    )

    # Standardize OS names
    def clean_os(os_str: str) -> str:
        os_lower = os_str.lower().strip()
        if "windows 11" in os_lower:
            return "Windows 11"
        elif "windows 10" in os_lower:
            return "Windows 10"
        elif "windows" in os_lower:
            return "Windows"
        elif "macos" in os_lower or "mac os" in os_lower:
            return "macOS"
        elif "chrome" in os_lower:
            return "Chrome OS"
        elif "linux" in os_lower or "ubuntu" in os_lower or "fedora" in os_lower:
            return "Linux"
        elif "dos" in os_lower:
            return "DOS"
        elif os_str.strip():
            return os_str.strip()
        return ""

    df["operating_system"] = df["operating_system"].apply(clean_os)

    # Ensure numeric fields are clean
    numeric_fields = [
        "screen_size_inches", "cpu_base_clock_ghz", "ram_gb",
        "storage_capacity_gb", "secondary_storage_gb", "gpu_vram_gb",
        "weight_kg", "battery_whr", "price_usd", "price_original",
        "refresh_rate_hz", "cpu_cores",
    ]
    for field in numeric_fields:
        df[field] = df[field].apply(lambda x: str(x).strip() if x else "")

    final_rows = len(df)
    logger.info(f"Validation: {initial_rows} -> {final_rows} rows ({initial_rows - final_rows} removed)")

    return df


def run_scrapers(
    max_per_site: int = 400,
    output_path: str = "data/raw/scraped_laptops.csv",
    platforms: List[str] = None,
) -> str:
    """Execute all scrapers and merge results into a single CSV.

    Args:
        max_per_site: Maximum products to collect per platform.
        output_path: Output CSV file path.
        platforms: List of platforms to scrape. Defaults to all three.

    Returns:
        Absolute path to the output CSV file.
    """
    logger = logging.getLogger(__name__)
    start_time = time.time()

    if platforms is None:
        platforms = ["flipkart", "amazon", "smartprix"]

    all_data: List[Dict[str, str]] = []

    # ── Flipkart ──
    if "flipkart" in platforms:
        try:
            logger.info("=" * 60)
            logger.info("Starting Flipkart scraper...")
            logger.info("=" * 60)
            scraper = FlipkartScraper()
            flipkart_data = scraper.scrape(max_products=max_per_site)
            all_data.extend(flipkart_data)
            logger.info(f"Flipkart: collected {len(flipkart_data)} laptops")
        except Exception as e:
            logger.error(f"Flipkart scraper failed: {e}", exc_info=True)

    # ── Amazon ──
    if "amazon" in platforms:
        try:
            logger.info("=" * 60)
            logger.info("Starting Amazon scraper...")
            logger.info("=" * 60)
            scraper = AmazonScraper()
            amazon_data = scraper.scrape(max_products=max_per_site)
            all_data.extend(amazon_data)
            logger.info(f"Amazon: collected {len(amazon_data)} laptops")
        except Exception as e:
            logger.error(f"Amazon scraper failed: {e}", exc_info=True)

    # ── Smartprix ──
    if "smartprix" in platforms:
        try:
            logger.info("=" * 60)
            logger.info("Starting Smartprix scraper...")
            logger.info("=" * 60)
            scraper = SmartprixScraper()
            smartprix_data = scraper.scrape(max_products=max_per_site)
            all_data.extend(smartprix_data)
            logger.info(f"Smartprix: collected {len(smartprix_data)} laptops")
        except Exception as e:
            logger.error(f"Smartprix scraper failed: {e}", exc_info=True)

    # ── Best Buy ──
    if "bestbuy" in platforms:
        try:
            logger.info("=" * 60)
            logger.info("Starting Best Buy scraper...")
            logger.info("=" * 60)
            scraper = BestBuyScraper()
            bestbuy_data = scraper.scrape(max_products=max_per_site)
            all_data.extend(bestbuy_data)
            logger.info(f"Best Buy: collected {len(bestbuy_data)} laptops")
        except Exception as e:
            logger.error(f"Best Buy scraper failed: {e}", exc_info=True)

    if not all_data:
        logger.error("No data collected from any platform!")
        return ""

    # ── Deduplicate ──
    logger.info(f"Total raw entries: {len(all_data)}")
    all_data = deduplicate_rows(all_data)
    logger.info(f"After deduplication: {len(all_data)}")

    # ── Validate and Clean ──
    df = validate_and_clean(all_data)

    # ── Add metadata columns ──
    df["scrape_timestamp"] = datetime.now(timezone.utc).isoformat()

    # ── Save ──
    output_abs = str(Path(project_root) / output_path)
    Path(output_abs).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_abs, index=False, encoding="utf-8")

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"SCRAPING COMPLETE")
    logger.info(f"  Total laptops:  {len(df)}")
    logger.info(f"  Columns:        {len(df.columns)}")
    logger.info(f"  Output:         {output_abs}")
    logger.info(f"  Elapsed:        {elapsed:.1f}s ({elapsed / 60:.1f} min)")
    logger.info("=" * 60)

    # Print column fill rates
    logger.info("\nColumn fill rates:")
    for col in df.columns:
        filled = (df[col] != "").sum()
        pct = filled / len(df) * 100 if len(df) > 0 else 0
        logger.info(f"  {col:30s} {filled:5d} / {len(df)} ({pct:5.1f}%)")

    return output_abs


def main():
    """CLI entrypoint for the laptop data scraper."""
    parser = argparse.ArgumentParser(
        description="Scrape laptop specifications from e-commerce platforms."
    )
    parser.add_argument(
        "--max-per-site",
        type=int,
        default=400,
        help="Maximum number of laptops to collect per platform (default: 400)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/scraped_laptops.csv",
        help="Output CSV file path (default: data/raw/scraped_laptops.csv)",
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["amazon", "flipkart", "smartprix", "bestbuy"],
        default=["flipkart", "amazon", "smartprix"],
        help="Platforms to scrape (default: flipkart amazon smartprix)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging verbosity (default: INFO)",
    )

    args = parser.parse_args()

    setup_logging(args.log_level)

    output_path = run_scrapers(
        max_per_site=args.max_per_site,
        output_path=args.output,
        platforms=args.platforms,
    )

    if output_path:
        print(f"\n✅ Dataset saved to: {output_path}")
    else:
        print("\n❌ Scraping failed. Check the log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
