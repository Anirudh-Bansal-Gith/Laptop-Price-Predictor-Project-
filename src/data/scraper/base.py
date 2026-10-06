"""Base scraper class with shared utilities for all e-commerce scrapers.

Provides:
- Session management with rotating User-Agents
- Exponential backoff retry logic
- Rate limiting to respect server load
- Common CPU/GPU specification parsing
- CSV output utilities
"""

import csv
import logging
import random
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

class DesktopUA:
    def __init__(self):
        self.agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        ]

    @property
    def random(self):
        return random.choice(self.agents)

_ua_engine = DesktopUA()

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for e-commerce laptop scrapers.

    Attributes:
        platform: Name of the e-commerce platform.
        session: Persistent HTTP session with rotating headers.
        min_delay: Minimum delay in seconds between requests.
        max_delay: Maximum delay in seconds between requests.
        max_retries: Maximum number of retry attempts per request.
    """

    # Standard columns (20+ features) every scraper should populate
    COLUMNS = [
        "source",               # 1.  E-commerce platform name
        "brand",                # 2.  Manufacturer (Dell, HP, Lenovo, etc.)
        "model_name",           # 3.  Full product model name
        "type_name",            # 4.  Form factor (Notebook, Ultrabook, Gaming, 2-in-1, etc.)
        "screen_size_inches",   # 5.  Diagonal display size
        "screen_resolution",    # 6.  Resolution string (e.g., '1920x1080')
        "display_type",         # 7.  Panel tech (IPS, OLED, TN, VA, etc.)
        "is_touchscreen",       # 8.  Touchscreen capability (1/0)
        "refresh_rate_hz",      # 9.  Display refresh rate in Hz
        "cpu_brand",            # 10. CPU manufacturer (Intel, AMD, Apple, Qualcomm)
        "cpu_family",           # 11. CPU product family (Core i7, Ryzen 5, M3, etc.)
        "cpu_model",            # 12. Specific CPU model (13700H, 7530U, etc.)
        "cpu_generation",       # 13. CPU generation number (12th, 13th, 14th, Zen 4, etc.)
        "cpu_base_clock_ghz",   # 14. Base clock speed in GHz
        "cpu_cores",            # 15. Number of CPU cores
        "ram_gb",               # 16. RAM capacity in GB
        "ram_type",             # 17. RAM technology (DDR4, DDR5, LPDDR5, etc.)
        "storage_capacity_gb",  # 18. Primary storage capacity in GB
        "storage_type",         # 19. Storage technology (SSD, HDD, eMMC, etc.)
        "secondary_storage_gb", # 20. Secondary storage capacity in GB (if present)
        "gpu_brand",            # 21. GPU manufacturer (Nvidia, AMD, Intel, Apple)
        "gpu_model",            # 22. GPU model name (RTX 4060, RX 7600M, Iris Xe, etc.)
        "gpu_vram_gb",          # 23. Dedicated GPU VRAM in GB
        "gpu_generation",       # 24. GPU architecture generation (Ada Lovelace, RDNA 3, etc.)
        "operating_system",     # 25. Pre-installed OS
        "weight_kg",            # 26. Weight in kilograms
        "battery_whr",          # 27. Battery capacity in Watt-hours
        "price_usd",            # 28. Price in USD
        "price_original",       # 29. Original price in source currency
        "currency",             # 30. Source currency code (USD, INR, etc.)
        "url",                  # 31. Product page URL
    ]

    def __init__(
        self,
        platform: str,
        min_delay: float = 0.5,
        max_delay: float = 1.5,
        max_retries: int = 3,
        timeout: int = 25,
    ):
        self.platform = platform
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self._ua = _ua_engine
        self.session = self._create_session()
        self._request_count = 0

    def _create_session(self) -> requests.Session:
        """Create a persistent session with browser-like headers."""
        session = requests.Session()
        session.headers.update(self._get_headers())
        return session

    def _get_headers(self) -> Dict[str, str]:
        """Generate browser-like HTTP headers with a rotated User-Agent."""
        return {
            "User-Agent": self._ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    def _rotate_headers(self) -> None:
        """Rotate the User-Agent to reduce detection probability."""
        self.session.headers.update({"User-Agent": self._ua.random})

    def _rate_limit(self) -> None:
        """Enforce a randomized delay between requests."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        self._request_count += 1
        # Rotate headers every 15 requests
        if self._request_count % 15 == 0:
            self._rotate_headers()
            logger.debug(f"[{self.platform}] Rotated User-Agent after {self._request_count} requests")

    def fetch_page(self, url: str, params: Optional[Dict] = None) -> Optional[BeautifulSoup]:
        """Fetch a URL with retry logic and exponential backoff.

        Args:
            url: Target URL to fetch.
            params: Optional query parameters.

        Returns:
            BeautifulSoup object of the page, or None if all retries fail.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                # Check for CAPTCHA / bot detection
                if self._is_blocked(response):
                    logger.warning(f"[{self.platform}] Bot detection triggered on attempt {attempt}")
                    self._rotate_headers()
                    time.sleep(random.uniform(5, 10))
                    continue

                return BeautifulSoup(response.content, "lxml")

            except requests.exceptions.HTTPError as e:
                status = response.status_code if response is not None else 0
                if status == 503:
                    logger.warning(f"[{self.platform}] 503 Service Unavailable, backing off...")
                    time.sleep(2 ** attempt * 2)
                elif status == 429:
                    logger.warning(f"[{self.platform}] 429 Rate Limited, backing off...")
                    time.sleep(2 ** attempt * 3)
                else:
                    logger.error(f"[{self.platform}] HTTP {status}: {e}")
                    time.sleep(2 ** attempt)

            except requests.exceptions.ConnectionError as e:
                logger.error(f"[{self.platform}] Connection error on attempt {attempt}: {e}")
                time.sleep(2 ** attempt * 2)

            except requests.exceptions.Timeout:
                logger.warning(f"[{self.platform}] Timeout on attempt {attempt} for {url}")
                time.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"[{self.platform}] Unexpected error: {e}")
                time.sleep(2 ** attempt)

        logger.error(f"[{self.platform}] All {self.max_retries} retries exhausted for {url}")
        return None

    def _is_blocked(self, response: requests.Response) -> bool:
        """Check if response is genuinely a bot-detection or CAPTCHA page."""
        if response.status_code in (403, 429):
            return True

        # If page is small and has bot challenge titles/phrases
        content = response.text.lower()
        if len(content) < 15000:
            block_signals = [
                "robot check",
                "type the characters you see",
                "enter the characters below",
                "<title>access denied",
                "<title>security check",
                "<title>just a moment...",
                "verify you are a human",
                "automated access to our services",
            ]
            return any(signal in content for signal in block_signals)

        return False

    # ──────────────────────────────────────────────────────────────
    # CPU Specification Parsing Utilities
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def parse_cpu_string(cpu_str: str) -> Dict[str, str]:
        """Extract CPU brand, family, model, generation, and base clock from a raw string.

        Examples:
            'Intel Core i7-13700H 2.4 GHz'  -> {brand: Intel, family: Core i7, model: 13700H, gen: 13th, clock: 2.4}
            'AMD Ryzen 7 7840HS'            -> {brand: AMD, family: Ryzen 7, model: 7840HS, gen: Zen 4, clock: ''}
            'Apple M3 Pro'                  -> {brand: Apple, family: M3, model: M3 Pro, gen: M3, clock: ''}

        Args:
            cpu_str: Raw CPU description string.

        Returns:
            Dict with keys: cpu_brand, cpu_family, cpu_model, cpu_generation, cpu_base_clock_ghz
        """
        result = {
            "cpu_brand": "",
            "cpu_family": "",
            "cpu_model": "",
            "cpu_generation": "",
            "cpu_base_clock_ghz": "",
        }

        if not cpu_str or cpu_str.strip() == "":
            return result

        cpu_str = str(cpu_str).strip()

        # Extract clock speed
        clock_match = re.search(r"(\d+\.?\d*)\s*GHz", cpu_str, re.IGNORECASE)
        if clock_match:
            result["cpu_base_clock_ghz"] = clock_match.group(1)

        # Direct generation mention (e.g., '14th Gen', '13th Generation', '12th Gen')
        gen_explicit = re.search(r"(\d{1,2})(?:th|rd|nd|st)?\s*Gen(?:eration)?", cpu_str, re.IGNORECASE)
        if gen_explicit:
            g_num = int(gen_explicit.group(1))
            g_suf = "th" if g_num >= 4 or g_num == 0 else ("rd" if g_num == 3 else ("nd" if g_num == 2 else "st"))
            result["cpu_generation"] = f"{g_num}{g_suf} Gen"

        # ── Intel ──
        if re.search(r"intel|core\s*i[3579]|core\s*ultra|celeron|pentium|atom|n\d{3,4}", cpu_str, re.IGNORECASE):
            result["cpu_brand"] = "Intel"

            # Core Ultra series (Meteor Lake+)
            ultra_match = re.search(r"Core\s+Ultra\s+(\d)\s*([-\s]?\s*\d{3}\w*)?", cpu_str, re.IGNORECASE)
            if ultra_match:
                result["cpu_family"] = f"Core Ultra {ultra_match.group(1)}"
                if ultra_match.group(2):
                    result["cpu_model"] = ultra_match.group(2).strip("- ")
                    first_digit = re.search(r"(\d)", result["cpu_model"])
                    if first_digit:
                        gen_map = {"1": "Meteor Lake", "2": "Arrow Lake", "3": "Panther Lake"}
                        result["cpu_generation"] = gen_map.get(first_digit.group(1), f"Gen {first_digit.group(1)}")
                elif not result["cpu_generation"]:
                    result["cpu_generation"] = "Meteor Lake"
                return result

            # Standard Core i-series (e.g., Core i7-13700H, i7 13700H, i5-12450H)
            core_match = re.search(r"(?:Core\s+)?(i[3579])\s*[-\s]?\s*(\d{4,5}\w*)", cpu_str, re.IGNORECASE)
            if core_match:
                result["cpu_family"] = f"Core {core_match.group(1).lower()}"
                model_num = core_match.group(2)
                result["cpu_model"] = model_num
                # Determine generation from model number if not already set
                if not result["cpu_generation"]:
                    digits_only = re.match(r"(\d+)", model_num)
                    if digits_only:
                        num_str = digits_only.group(1)
                        if len(num_str) >= 5:
                            gen_num = num_str[:2]
                        else:
                            gen_num = num_str[0]
                        try:
                            gen_int = int(gen_num)
                            suffix = "th" if gen_int >= 4 or gen_int == 0 else ("rd" if gen_int == 3 else ("nd" if gen_int == 2 else "st"))
                            result["cpu_generation"] = f"{gen_int}{suffix} Gen"
                        except ValueError:
                            pass
                return result

            # Core i-series with separate model mention
            core_simple = re.search(r"(?:Core\s+)?(i[3579])", cpu_str, re.IGNORECASE)
            if core_simple:
                result["cpu_family"] = f"Core {core_simple.group(1).lower()}"

            # Core 3/5/7 series (Intel Core 5 120U / 210H)
            core_new = re.search(r"Core\s+([3579])\s*[-\s]?\s*(\d{3,4}\w*)?", cpu_str, re.IGNORECASE)
            if core_new:
                result["cpu_family"] = f"Core {core_new.group(1)}"
                if core_new.group(2):
                    result["cpu_model"] = core_new.group(2)
                if not result["cpu_generation"]:
                    result["cpu_generation"] = "Raptor Lake Refresh"
                return result

            # Budget Intel (Celeron, Pentium, N-series)
            budget_match = re.search(r"(Celeron|Pentium|Atom|N\d{4})\s*(\w*)", cpu_str, re.IGNORECASE)
            if budget_match:
                result["cpu_family"] = budget_match.group(1).title()
                result["cpu_model"] = budget_match.group(2) if budget_match.group(2) else budget_match.group(1)
                result["cpu_generation"] = "Budget"
                return result

        # ── AMD ──
        elif re.search(r"amd|ryzen|athlon", cpu_str, re.IGNORECASE):
            result["cpu_brand"] = "AMD"

            # Ryzen AI series
            ai_match = re.search(r"Ryzen\s+AI\s+(\d)\s*(\w*)", cpu_str, re.IGNORECASE)
            if ai_match:
                result["cpu_family"] = f"Ryzen AI {ai_match.group(1)}"
                result["cpu_model"] = ai_match.group(2)
                result["cpu_generation"] = "Zen 5 (Strix)"
                return result

            # Ryzen standard
            ryzen_match = re.search(r"Ryzen\s+(\d)(?:\s*(?:Quad|Octa|Hexa|Dual)?\s*Core)?(?:\s*Processor)?\s*([-\s]?\s*\d{4}\w*)?", cpu_str, re.IGNORECASE)
            if ryzen_match:
                result["cpu_family"] = f"Ryzen {ryzen_match.group(1)}"
                if ryzen_match.group(2):
                    model = ryzen_match.group(2).strip("- ")
                    result["cpu_model"] = model
                    first_digit = model[0]
                    gen_map = {
                        "1": "Zen", "2": "Zen+", "3": "Zen 2",
                        "4": "Zen 2 (APU)", "5": "Zen 3", "6": "Zen 3+",
                        "7": "Zen 4", "8": "Zen 4", "9": "Zen 5",
                    }
                    if not result["cpu_generation"]:
                        result["cpu_generation"] = gen_map.get(first_digit, f"Ryzen Gen {first_digit}")
                return result

            # AMD Athlon
            a_match = re.search(r"(A\d{1,2}|Athlon)\s*[-\s]?\s*(\w*)", cpu_str, re.IGNORECASE)
            if a_match:
                result["cpu_family"] = a_match.group(1).upper()
                result["cpu_model"] = a_match.group(2) if a_match.group(2) else a_match.group(1)
                result["cpu_generation"] = "AMD Budget"
                return result

        # ── Apple Silicon ──
        elif re.search(r"apple|m[1-4]", cpu_str, re.IGNORECASE):
            result["cpu_brand"] = "Apple"
            m_match = re.search(r"(M[1-4])\s*(Pro|Max|Ultra)?", cpu_str, re.IGNORECASE)
            if m_match:
                chip = m_match.group(1).upper()
                variant = m_match.group(2) or ""
                result["cpu_family"] = chip
                result["cpu_model"] = f"{chip} {variant}".strip()
                result["cpu_generation"] = chip
                return result

        # ── Qualcomm ──
        elif re.search(r"qualcomm|snapdragon", cpu_str, re.IGNORECASE):
            result["cpu_brand"] = "Qualcomm"
            snap_match = re.search(r"Snapdragon\s+(\w+)\s*(\w*)", cpu_str, re.IGNORECASE)
            if snap_match:
                result["cpu_family"] = f"Snapdragon {snap_match.group(1)}"
                result["cpu_model"] = snap_match.group(2) if snap_match.group(2) else snap_match.group(1)
                result["cpu_generation"] = "Snapdragon"
                return result

        # Fallback: try to extract anything useful
        if len(cpu_str) < 40 and not any(k in cpu_str.lower() for k in ["laptop", "notebook", "ssd", "ram", "gb"]):
            result["cpu_model"] = cpu_str
        return result

    @staticmethod
    def parse_gpu_string(gpu_str: str) -> Dict[str, str]:
        """Extract GPU brand, model, VRAM, and generation from a raw string.

        Examples:
            'NVIDIA GeForce RTX 4060 8GB'  -> {brand: Nvidia, model: RTX 4060, vram: 8, gen: Ada Lovelace}
            'AMD Radeon RX 7600M XT'       -> {brand: AMD, model: RX 7600M XT, vram: '', gen: RDNA 3}
            'Intel Iris Xe Graphics'       -> {brand: Intel, model: Iris Xe, vram: '', gen: Integrated}

        Args:
            gpu_str: Raw GPU description string.

        Returns:
            Dict with keys: gpu_brand, gpu_model, gpu_vram_gb, gpu_generation
        """
        result = {
            "gpu_brand": "",
            "gpu_model": "",
            "gpu_vram_gb": "",
            "gpu_generation": "",
        }

        if not gpu_str or str(gpu_str).strip() == "":
            return result

        gpu_str = str(gpu_str).strip()

        # Extract VRAM
        vram_match = re.search(r"(\d+)\s*GB", gpu_str, re.IGNORECASE)
        if vram_match:
            result["gpu_vram_gb"] = vram_match.group(1)

        # ── NVIDIA ──
        if re.search(r"nvidia|geforce|rtx|gtx|quadro", gpu_str, re.IGNORECASE):
            result["gpu_brand"] = "Nvidia"

            # RTX 40xx / 50xx (Ada Lovelace / Blackwell)
            rtx_match = re.search(r"RTX\s*(\d{4})\s*(Ti|SUPER)?", gpu_str, re.IGNORECASE)
            if rtx_match:
                model_num = rtx_match.group(1)
                suffix = f" {rtx_match.group(2)}" if rtx_match.group(2) else ""
                result["gpu_model"] = f"RTX {model_num}{suffix}"
                first_digit = model_num[0]
                gen_map = {"2": "Turing", "3": "Ampere", "4": "Ada Lovelace", "5": "Blackwell"}
                result["gpu_generation"] = gen_map.get(first_digit, f"RTX Gen {first_digit}")
                return result

            # GTX series
            gtx_match = re.search(r"GTX\s*(\d{3,4})\s*(Ti)?", gpu_str, re.IGNORECASE)
            if gtx_match:
                model_num = gtx_match.group(1)
                suffix = f" {gtx_match.group(2)}" if gtx_match.group(2) else ""
                result["gpu_model"] = f"GTX {model_num}{suffix}"
                first_digit = model_num[0]
                gen_map = {"9": "Maxwell", "1": "Pascal", "6": "Turing (16xx)"}
                if len(model_num) == 4 and model_num[:2] == "16":
                    result["gpu_generation"] = "Turing"
                else:
                    result["gpu_generation"] = gen_map.get(first_digit, f"GTX Gen {first_digit}")
                return result

            # MX series (entry-level discrete)
            mx_match = re.search(r"MX\s*(\d{3,4})", gpu_str, re.IGNORECASE)
            if mx_match:
                result["gpu_model"] = f"MX {mx_match.group(1)}"
                result["gpu_generation"] = "Entry Discrete"
                return result

            # Quadro
            quadro_match = re.search(r"Quadro\s+(\w+)", gpu_str, re.IGNORECASE)
            if quadro_match:
                result["gpu_model"] = f"Quadro {quadro_match.group(1)}"
                result["gpu_generation"] = "Professional"
                return result

        # ── AMD ──
        elif re.search(r"amd|radeon", gpu_str, re.IGNORECASE):
            result["gpu_brand"] = "AMD"

            rx_match = re.search(r"RX\s*(\d{4})\s*(\w*)", gpu_str, re.IGNORECASE)
            if rx_match:
                model_num = rx_match.group(1)
                suffix = f" {rx_match.group(2)}" if rx_match.group(2) else ""
                result["gpu_model"] = f"RX {model_num}{suffix}".strip()
                first_digit = model_num[0]
                gen_map = {"5": "RDNA 1", "6": "RDNA 2", "7": "RDNA 3", "8": "RDNA 4", "9": "RDNA 4+"}
                result["gpu_generation"] = gen_map.get(first_digit, f"RX Gen {first_digit}")
                return result

            # Radeon integrated
            rad_match = re.search(r"Radeon\s+([\w\s]+)", gpu_str, re.IGNORECASE)
            if rad_match:
                result["gpu_model"] = rad_match.group(1).strip()
                result["gpu_generation"] = "Integrated"
                return result

        # ── Intel Integrated ──
        elif re.search(r"intel|iris|uhd|hd graphics", gpu_str, re.IGNORECASE):
            result["gpu_brand"] = "Intel"

            arc_match = re.search(r"Arc\s+(\w+)", gpu_str, re.IGNORECASE)
            if arc_match:
                result["gpu_model"] = f"Arc {arc_match.group(1)}"
                result["gpu_generation"] = "Alchemist"
                return result

            iris_match = re.search(r"(Iris\s+(?:Xe|Plus|Pro)?)\s*(Graphics)?\s*(\w*)", gpu_str, re.IGNORECASE)
            if iris_match:
                result["gpu_model"] = iris_match.group(1).strip()
                result["gpu_generation"] = "Integrated"
                return result

            uhd_match = re.search(r"(UHD|HD)\s*(?:Graphics)?\s*(\d*)", gpu_str, re.IGNORECASE)
            if uhd_match:
                model = f"{uhd_match.group(1)} Graphics"
                if uhd_match.group(2):
                    model += f" {uhd_match.group(2)}"
                result["gpu_model"] = model
                result["gpu_generation"] = "Integrated"
                return result

        # ── Apple ──
        elif re.search(r"apple|m[1-4]", gpu_str, re.IGNORECASE):
            result["gpu_brand"] = "Apple"
            m_match = re.search(r"(M[1-4])\s*(Pro|Max|Ultra)?", gpu_str, re.IGNORECASE)
            if m_match:
                chip = m_match.group(1).upper()
                variant = m_match.group(2) or ""
                result["gpu_model"] = f"{chip} {variant} GPU".strip()
                result["gpu_generation"] = chip
                return result

        if len(gpu_str) < 40 and not any(k in gpu_str.lower() for k in ["laptop", "notebook", "desktop", "inch", "windows"]):
            result["gpu_model"] = gpu_str
        return result

    @staticmethod
    def parse_storage(storage_str: str) -> Tuple[str, str, str]:
        """Parse storage string into capacity, type, and secondary storage.

        Args:
            storage_str: Raw storage specification string.

        Returns:
            Tuple of (capacity_gb, storage_type, secondary_storage_gb).
        """
        capacity_gb = ""
        storage_type = ""
        secondary_gb = ""

        if not storage_str:
            return capacity_gb, storage_type, secondary_gb

        storage_str = str(storage_str)

        # 1. Look for explicit storage mentions (e.g. 512GB SSD, 1TB NVMe, 256 GB eMMC)
        matches = re.findall(
            r"(\d+\.?\d*)\s*(TB|GB)\s*(?:M\.2\s*|NVMe\s*|PCIe\s*|Gen\s*\d\s*)?(SSD|HDD|eMMC|Flash|NVMe|PCIe|SATA|ROM|Storage)?",
            storage_str, re.IGNORECASE
        )

        valid_storage = []
        for size, unit, stype in matches:
            # Ignore VRAM or RAM mentions
            size_float = float(size)
            size_gb = int(size_float * 1000 if unit.upper() == "TB" else size_float)

            # Skip small sizes (< 64 GB) unless explicitly eMMC/Flash
            if size_gb < 64 and not (stype and any(k in stype.lower() for k in ["emmc", "flash"])):
                continue

            if not stype:
                lower = storage_str.lower()
                if "ssd" in lower or "nvme" in lower or "pcie" in lower:
                    stype = "SSD"
                elif "hdd" in lower:
                    stype = "HDD"
                elif "emmc" in lower:
                    stype = "eMMC"
                else:
                    stype = "SSD"

            valid_storage.append((str(size_gb), stype.upper()))

        if valid_storage:
            capacity_gb, storage_type = valid_storage[0]
            if len(valid_storage) > 1:
                secondary_gb = valid_storage[1][0]

        return capacity_gb, storage_type, secondary_gb

    @staticmethod
    def parse_ram(ram_str: str) -> Tuple[str, str]:
        """Parse RAM string into capacity and type.

        Args:
            ram_str: Raw RAM specification string.

        Returns:
            Tuple of (ram_gb, ram_type).
        """
        ram_gb = ""
        ram_type = ""

        if not ram_str:
            return ram_gb, ram_type

        ram_str = str(ram_str)

        # Type match first
        type_match = re.search(r"(LPDDR5X|LPDDR5|LPDDR4X|LPDDR4|LPDDR3|DDR5|DDR4|DDR3)", ram_str, re.IGNORECASE)
        if type_match:
            ram_type = type_match.group(1).upper()

        # Capacity match with RAM or DDR context
        ram_m = re.search(r"(\d+)\s*GB\s*(?:(?:L?P?DDR\d?X?|Unified\s*Memory|RAM)\b|(?=[,\s/]+\d+\s*(?:GB|TB)\s*SSD))", ram_str, re.IGNORECASE)
        if ram_m:
            ram_gb = ram_m.group(1)
        else:
            # Fallback: look for typical RAM sizes (4, 8, 12, 16, 24, 32, 64)
            # but ensure not followed by SSD/HDD/eMMC/Storage/VRAM
            candidates = re.findall(r"\b(4|8|12|16|24|32|64)\s*GB\b(?!\s*(?:SSD|HDD|eMMC|Storage|ROM|VRAM|RTX|GTX))", ram_str, re.IGNORECASE)
            if candidates:
                ram_gb = candidates[0]

        return ram_gb, ram_type

    @staticmethod
    def parse_weight(weight_str: str) -> str:
        """Parse weight string into kilograms.

        Args:
            weight_str: Raw weight string (may include lbs or kg).

        Returns:
            Weight in kg as a string, or empty string.
        """
        if not weight_str:
            return ""

        weight_str = str(weight_str)

        kg_match = re.search(r"(\d+\.?\d*)\s*kg", weight_str, re.IGNORECASE)
        if kg_match:
            return kg_match.group(1)

        lbs_match = re.search(r"(\d+\.?\d*)\s*(lbs?|pounds?)", weight_str, re.IGNORECASE)
        if lbs_match:
            return f"{float(lbs_match.group(1)) * 0.453592:.2f}"

        return ""

    @staticmethod
    def parse_price(price_str: str) -> Tuple[str, str]:
        """Parse price string into numeric value and currency.

        Args:
            price_str: Raw price string with currency symbols.

        Returns:
            Tuple of (price_numeric, currency_code).
        """
        if not price_str:
            return "", ""

        price_str = str(price_str).strip()

        # Detect currency
        currency = "USD"
        if "₹" in price_str or "inr" in price_str.lower():
            currency = "INR"
        elif "€" in price_str or "eur" in price_str.lower():
            currency = "EUR"
        elif "£" in price_str or "gbp" in price_str.lower():
            currency = "GBP"

        # Extract numeric value
        clean = re.sub(r"[^\d.,]", "", price_str)
        # Handle Indian/European number formatting
        if currency == "INR":
            clean = clean.replace(",", "")
        elif "," in clean and "." in clean:
            # Standard: 1,299.99
            clean = clean.replace(",", "")
        elif "," in clean:
            # Could be European (1.299,99) or simple (1,299)
            parts = clean.split(",")
            if len(parts[-1]) == 2:
                clean = clean.replace(".", "").replace(",", ".")
            else:
                clean = clean.replace(",", "")

        try:
            return f"{float(clean):.2f}", currency
        except (ValueError, TypeError):
            return "", currency

    @classmethod
    def parse_title_features(cls, text: str, row: Dict[str, str]) -> Dict[str, str]:
        """Extract missing features from title or combined specification text.

        Fills in missing row fields using regex pattern matching on the full
        product title and description.
        """
        if not text:
            return row

        # ── Brand ──
        if not row["brand"]:
            brands = [
                "HP", "Dell", "Lenovo", "Asus", "Acer", "Apple", "MSI", "Samsung",
                "Microsoft", "LG", "Razer", "Gigabyte", "Alienware", "Infinix",
                "Xiaomi", "RedmiBook", "Realme", "Honor", "Chuwi", "Avita",
                "Primebook", "Ultimus", "Wings", "Thomson", "Nokia", "AXL", "Framework"
            ]
            for b in brands:
                if re.search(r"\b" + re.escape(b) + r"\b", text, re.IGNORECASE):
                    row["brand"] = b
                    break

        # ── Form Factor / Type ──
        if not row["type_name"]:
            t_lower = text.lower()
            if "gaming" in t_lower:
                row["type_name"] = "Gaming"
            elif any(k in t_lower for k in ["2 in 1", "2-in-1", "convertible", "x360", "yoga", "flip"]):
                row["type_name"] = "2-in-1"
            elif any(k in t_lower for k in ["chromebook", "chrome book"]):
                row["type_name"] = "Chromebook"
            elif any(k in t_lower for k in ["ultrabook", "macbook", "thin & light", "thin and light", "slim", "zenbook", "swift", "gram"]):
                row["type_name"] = "Ultrabook"
            elif "workstation" in t_lower:
                row["type_name"] = "Workstation"
            else:
                row["type_name"] = "Notebook"

        # ── Screen Size ──
        if not row["screen_size_inches"]:
            # e.g. 15.6", 15.6 inch, 14-inch, 39.62 cm (15.6 Inch)
            size_m = re.search(r"(\d{1,2}(?:\.\d{1,2})?)\s*(?:inch|\"|[- ]in\b|cm\s*\(([\d.]+)\s*inch)", text, re.IGNORECASE)
            if size_m:
                val = size_m.group(2) if size_m.group(2) else size_m.group(1)
                try:
                    f_val = float(val)
                    if 10.0 <= f_val <= 18.5:
                        row["screen_size_inches"] = str(round(f_val, 1))
                except ValueError:
                    pass

        # ── Resolution ──
        if not row["screen_resolution"]:
            res_m = re.search(r"(\d{3,4}\s*[xX*×]\s*\d{3,4})", text)
            if res_m:
                row["screen_resolution"] = re.sub(r"\s*", "", res_m.group(1)).replace("X", "x").replace("×", "x").replace("*", "x")
            elif re.search(r"\b4K\b|UHD\b", text, re.IGNORECASE):
                row["screen_resolution"] = "3840x2160"
            elif re.search(r"\bQHD\b|\b2\.5K\b|\b2K\b", text, re.IGNORECASE):
                row["screen_resolution"] = "2560x1440"
            elif re.search(r"\bWUXGA\b", text, re.IGNORECASE):
                row["screen_resolution"] = "1920x1200"
            elif re.search(r"\bWQXGA\b", text, re.IGNORECASE):
                row["screen_resolution"] = "2560x1600"
            elif re.search(r"\bFHD\b|Full\s*HD", text, re.IGNORECASE):
                row["screen_resolution"] = "1920x1080"
            elif re.search(r"\bHD\b", text, re.IGNORECASE):
                row["screen_resolution"] = "1366x768"

        # ── Display Type ──
        if not row["display_type"]:
            if re.search(r"\bOLED\b", text, re.IGNORECASE):
                row["display_type"] = "OLED"
            elif re.search(r"\bAMOLED\b", text, re.IGNORECASE):
                row["display_type"] = "AMOLED"
            elif re.search(r"\bIPS\b", text, re.IGNORECASE):
                row["display_type"] = "IPS"
            elif re.search(r"Retina", text, re.IGNORECASE):
                row["display_type"] = "Retina"
            elif re.search(r"Anti-Glare", text, re.IGNORECASE):
                row["display_type"] = "Anti-Glare"

        # ── Touchscreen ──
        if not row["is_touchscreen"]:
            if re.search(r"touch\s*screen|touchscreen|\btouch\b|2-in-1|2 in 1|x360|yoga|flip", text, re.IGNORECASE):
                row["is_touchscreen"] = "1"
            else:
                row["is_touchscreen"] = "0"

        # ── Refresh Rate ──
        if not row["refresh_rate_hz"]:
            rr_m = re.search(r"(\d{2,3})\s*Hz\b", text, re.IGNORECASE)
            if rr_m:
                row["refresh_rate_hz"] = rr_m.group(1)

        # ── CPU Specs ──
        cpu_dict = cls.parse_cpu_string(text)
        for k, v in cpu_dict.items():
            if not row[k] and v:
                row[k] = v

        # CPU Cores
        if not row["cpu_cores"]:
            cores_m = re.search(r"(\d{1,2})\s*[- ]?Cores?\b", text, re.IGNORECASE)
            if cores_m:
                row["cpu_cores"] = cores_m.group(1)
            elif re.search(r"Octa\s*Core", text, re.IGNORECASE):
                row["cpu_cores"] = "8"
            elif re.search(r"Hexa\s*Core", text, re.IGNORECASE):
                row["cpu_cores"] = "6"
            elif re.search(r"Quad\s*Core", text, re.IGNORECASE):
                row["cpu_cores"] = "4"
            elif re.search(r"Dual\s*Core", text, re.IGNORECASE):
                row["cpu_cores"] = "2"

        # ── RAM Specs ──
        if not row["ram_gb"]:
            ram_gb, ram_type = cls.parse_ram(text)
            if ram_gb:
                row["ram_gb"] = ram_gb
            if ram_type and not row["ram_type"]:
                row["ram_type"] = ram_type
        elif not row["ram_type"]:
            _, ram_type = cls.parse_ram(text)
            if ram_type:
                row["ram_type"] = ram_type

        # ── Storage Specs ──
        if not row["storage_capacity_gb"]:
            cap, stype, sec = cls.parse_storage(text)
            if cap:
                row["storage_capacity_gb"] = cap
            if stype and not row["storage_type"]:
                row["storage_type"] = stype
            if sec and not row["secondary_storage_gb"]:
                row["secondary_storage_gb"] = sec

        # ── GPU Specs ──
        gpu_dict = cls.parse_gpu_string(text)
        for k, v in gpu_dict.items():
            if not row[k] and v:
                row[k] = v

        # Fallback to integrated GPU if discrete GPU not found
        if not row["gpu_model"]:
            if row["cpu_brand"] == "Intel":
                row["gpu_brand"] = "Intel"
                row["gpu_model"] = "Intel Iris Xe Graphics" if "Core i" in row.get("cpu_family", "") else "Intel UHD Graphics"
                row["gpu_generation"] = "Integrated"
            elif row["cpu_brand"] == "AMD":
                row["gpu_brand"] = "AMD"
                row["gpu_model"] = "AMD Radeon Graphics"
                row["gpu_generation"] = "Integrated"
            elif row["cpu_brand"] == "Apple":
                row["gpu_brand"] = "Apple"
                row["gpu_model"] = f"{row.get('cpu_family', 'Apple')} GPU"
                row["gpu_generation"] = row.get("cpu_family", "Apple Silicon")

        # ── Operating System ──
        if not row["operating_system"]:
            t_low = text.lower()
            if "win 11" in t_low or "windows 11" in t_low:
                row["operating_system"] = "Windows 11"
            elif "win 10" in t_low or "windows 10" in t_low:
                row["operating_system"] = "Windows 10"
            elif "macos" in t_low or "mac os" in t_low or row["brand"] == "Apple":
                row["operating_system"] = "macOS"
            elif "chrome" in t_low or row["type_name"] == "Chromebook":
                row["operating_system"] = "Chrome OS"
            elif "linux" in t_low or "ubuntu" in t_low:
                row["operating_system"] = "Linux"
            elif "dos" in t_low:
                row["operating_system"] = "DOS"

        # ── Weight ──
        if not row["weight_kg"]:
            row["weight_kg"] = cls.parse_weight(text)

        return row

    def empty_row(self) -> Dict[str, str]:
        """Return a row dict with all columns set to empty strings."""
        return {col: "" for col in self.COLUMNS}

    @abstractmethod
    def scrape(self, max_products: int = 400) -> List[Dict[str, str]]:
        """Scrape laptop data from the platform.

        Args:
            max_products: Maximum number of laptop entries to collect.

        Returns:
            List of dicts, each containing column values from COLUMNS.
        """
        ...

    @staticmethod
    def save_to_csv(data: List[Dict[str, str]], filepath: str, columns: List[str]) -> None:
        """Write scraped data to a CSV file.

        Args:
            data: List of row dictionaries.
            filepath: Output CSV file path.
            columns: Ordered list of column names.
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Saved {len(data)} rows to {filepath}")
