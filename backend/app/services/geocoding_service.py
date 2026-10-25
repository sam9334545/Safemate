"""Geocoding service integrating OpenStreetMap Nominatim with caching and resilient fallbacks."""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple
import httpx

from app.schemas.routes import GeocodeItem

logger = logging.getLogger(__name__)

# Sample offline landmarks for instant demo and offline reliability
SAMPLE_GEOCODE_FIXTURES: List[Dict[str, Any]] = [
    {
        "query_keys": ["connaught place", "cp", "central park delhi", "rajiv chowk"],
        "display_name": "Connaught Place, Inner Circle, New Delhi, Delhi, 110001, India",
        "name": "Connaught Place",
        "lat": 28.6315,
        "lon": 77.2167,
        "place_type": "commercial",
    },
    {
        "query_keys": ["india gate", "kartavya path"],
        "display_name": "India Gate, Rajpath, India Gate Lawns, New Delhi, Delhi, 110001, India",
        "name": "India Gate",
        "lat": 28.6129,
        "lon": 77.2295,
        "place_type": "monument",
    },
    {
        "query_keys": ["hauz khas", "hauz khas village", "hkv"],
        "display_name": "Hauz Khas Village, Sri Aurobindo Marg, New Delhi, Delhi, 110016, India",
        "name": "Hauz Khas Village",
        "lat": 28.5494,
        "lon": 77.1936,
        "place_type": "suburb",
    },
    {
        "query_keys": ["south extension", "south ex", "ndse"],
        "display_name": "South Extension Part II, Ring Road, New Delhi, Delhi, 110049, India",
        "name": "South Extension",
        "lat": 28.5689,
        "lon": 77.2223,
        "place_type": "commercial",
    },
    {
        "query_keys": ["lajpat nagar", "central market"],
        "display_name": "Lajpat Nagar Central Market, New Delhi, Delhi, 110024, India",
        "name": "Lajpat Nagar Market",
        "lat": 28.5700,
        "lon": 77.2373,
        "place_type": "market",
    },
    {
        "query_keys": ["saket", "select citywalk", "saket district centre"],
        "display_name": "Select Citywalk, Saket District Centre, Sector 6, Pushp Vihar, New Delhi, Delhi 110017",
        "name": "Select Citywalk Saket",
        "lat": 28.5283,
        "lon": 77.2190,
        "place_type": "commercial",
    },
    {
        "query_keys": ["cyber hub", "dlf cyber city", "gurgaon"],
        "display_name": "DLF Cyber Hub, DLF Phase 2, Sector 24, Gurugram, Haryana 122002",
        "name": "DLF Cyber Hub",
        "lat": 28.4950,
        "lon": 77.0895,
        "place_type": "commercial",
    },
    {
        "query_keys": ["north campus", "delhi university", "vishwavidyalaya"],
        "display_name": "Delhi University North Campus, Chhatra Marg, University Enclave, Delhi 110007",
        "name": "Delhi University North Campus",
        "lat": 28.6903,
        "lon": 77.2066,
        "place_type": "education",
    },
]


class GeocodingService:
    """Provides forward and reverse geocoding with caching, rate-limit courtesy, and fallbacks."""

    def __init__(self, user_agent: str = "SafeMate-WomenSafetyApp/1.0"):
        self.user_agent = user_agent
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.reverse_url = "https://nominatim.openstreetmap.org/reverse"
        self._cache: Dict[str, Tuple[float, List[GeocodeItem]]] = {}
        self._cache_ttl_seconds = 3600.0  # 1 hour
        self._last_request_time = 0.0

    async def _rate_limit_wait(self) -> None:
        """Adhere strictly to Nominatim's 1 request per second policy."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < 1.05:
            import asyncio
            await asyncio.sleep(1.05 - elapsed)
        self._last_request_time = time.time()

    def _match_offline_fixtures(self, query: str) -> List[GeocodeItem]:
        q_lower = query.lower().strip()
        matches = []
        for fixture in SAMPLE_GEOCODE_FIXTURES:
            if any(k in q_lower or q_lower in k for k in fixture["query_keys"]):
                matches.append(
                    GeocodeItem(
                        display_name=fixture["display_name"],
                        name=fixture["name"],
                        latitude=fixture["lat"],
                        longitude=fixture["lon"],
                        place_type=fixture["place_type"],
                    )
                )
        return matches

    async def geocode(self, query: str, limit: int = 5) -> List[GeocodeItem]:
        """Search address or place name and return suggestions."""
        clean_q = query.strip()
        if not clean_q or len(clean_q) < 2:
            return []

        # Check memory cache
        cache_key = f"geo:{clean_q.lower()}:{limit}"
        now = time.time()
        if cache_key in self._cache:
            ts, items = self._cache[cache_key]
            if now - ts < self._cache_ttl_seconds:
                return items

        results: List[GeocodeItem] = []

        # Try Nominatim external API
        try:
            await self._rate_limit_wait()
            async with httpx.AsyncClient(timeout=4.0) as client:
                headers = {"User-Agent": self.user_agent, "Accept-Language": "en"}
                params = {
                    "q": clean_q,
                    "format": "json",
                    "addressdetails": "1",
                    "limit": str(limit),
                }
                resp = await client.get(self.nominatim_url, headers=headers, params=params)
                if resp.status_code == 200:
                    raw_data = resp.json()
                    for item in raw_data:
                        disp = item.get("display_name", "")
                        name = item.get("name") or disp.split(",")[0].strip()
                        lat = float(item["lat"])
                        lon = float(item["lon"])
                        place_type = item.get("type") or item.get("class")
                        results.append(
                            GeocodeItem(
                                display_name=disp,
                                name=name,
                                latitude=lat,
                                longitude=lon,
                                place_type=place_type,
                            )
                        )
        except Exception as exc:
            logger.warning(f"Nominatim geocoding failed for '{clean_q}': {type(exc).__name__}: {exc}")

        # If external returned nothing or failed, check offline fixtures
        if not results:
            fixture_matches = self._match_offline_fixtures(clean_q)
            if fixture_matches:
                results.extend(fixture_matches[:limit])

        # If still nothing, return a fallback approximate item if coordinates are mentioned or generic label
        if not results and "," in clean_q:
            parts = clean_q.split(",")
            if len(parts) == 2:
                try:
                    p_lat = float(parts[0].strip())
                    p_lon = float(parts[1].strip())
                    if -90 <= p_lat <= 90 and -180 <= p_lon <= 180:
                        results.append(
                            GeocodeItem(
                                display_name=f"Custom Point ({p_lat:.4f}, {p_lon:.4f})",
                                name="Custom Point",
                                latitude=p_lat,
                                longitude=p_lon,
                                place_type="coordinate",
                            )
                        )
                except ValueError:
                    pass

        # Save to cache
        if results:
            self._cache[cache_key] = (now, results)

        return results

    async def reverse_geocode(self, lat: float, lon: float) -> GeocodeItem:
        """Reverse geocode latitude and longitude into an address description."""
        cache_key = f"rev:{lat:.4f}:{lon:.4f}"
        now = time.time()
        if cache_key in self._cache:
            ts, items = self._cache[cache_key]
            if now - ts < self._cache_ttl_seconds and items:
                return items[0]

        # Check proximity to known fixtures
        for fix in SAMPLE_GEOCODE_FIXTURES:
            if abs(fix["lat"] - lat) < 0.005 and abs(fix["lon"] - lon) < 0.005:
                item = GeocodeItem(
                    display_name=fix["display_name"],
                    name=fix["name"],
                    latitude=lat,
                    longitude=lon,
                    place_type=fix["place_type"],
                )
                self._cache[cache_key] = (now, [item])
                return item

        try:
            await self._rate_limit_wait()
            async with httpx.AsyncClient(timeout=4.0) as client:
                headers = {"User-Agent": self.user_agent, "Accept-Language": "en"}
                params = {"lat": str(lat), "lon": str(lon), "format": "json"}
                resp = await client.get(self.reverse_url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    disp = data.get("display_name", f"Location ({lat:.4f}, {lon:.4f})")
                    name = data.get("name") or disp.split(",")[0].strip()
                    item = GeocodeItem(
                        display_name=disp,
                        name=name,
                        latitude=lat,
                        longitude=lon,
                        place_type=data.get("type"),
                    )
                    self._cache[cache_key] = (now, [item])
                    return item
        except Exception as exc:
            logger.warning(f"Reverse geocoding failed: {exc}")

        # Fallback
        fallback = GeocodeItem(
            display_name=f"Location near {lat:.4f}, {lon:.4f}",
            name=f"{lat:.4f}, {lon:.4f}",
            latitude=lat,
            longitude=lon,
            place_type="coordinate",
        )
        self._cache[cache_key] = (now, [fallback])
        return fallback


geocoding_service = GeocodingService()
