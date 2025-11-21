"""
Robust Dhaka POI scraper using OpenStreetMap Overpass API.

What it does:
- Tries several area-name lookups for Dhaka. If none match, falls back to a bounding box covering Greater Dhaka.
- Optionally tiles the bbox into a grid to reduce Overpass load and increase coverage.
- Queries nodes/ways/relations for categories: hospital, bank, school, college, university, hotel, restaurant, park.
- Extracts name, tags, coords (lat/lon), osm_type/id and saves to an XLSX with one sheet "pois" and separate sheets per category.
- Deduplicates results.

Requirements:
    pip install requests pandas openpyxl

Run:
    python dhaka_overpass_dhaka_fixed.py
"""

import requests
import time
import pandas as pd
from typing import List, Dict, Tuple, Optional
import math

# Overpass endpoint (try main; user can change to a mirror if rate-limited)
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Try a list of area names common in OSM for Dhaka. If none found, we'll use fallback bbox.
AREA_NAME_CANDIDATES = [
    "Dhaka",
    "Dhaka District",
    "Dhaka Metropolitan",
    "Dhaka City",
    "Dhaka North",
    "Dhaka South",
]d

# Fallback bounding box for Greater Dhaka (south, west, north, east).
# This covers central and greater Dhaka; you can adjust if you want larger/smaller.
FALLBACK_BBOX = (23.60, 90.20, 24.00, 90.60)  # (minlat, minlon, maxlat, maxlon)

# Tile size in degrees for bbox tiling (smaller -> more Overpass queries). Adjust if you get rate limits.
TILE_DEG = 0.05  # ~5-6 km per tile (latitude), smaller is safer for coverage

# Categories and OSM tag clauses (node/way/relation)
CATEGORIES = {
    "hospital":      ('node["amenity"="hospital"]', 'way["amenity"="hospital"]', 'relation["amenity"="hospital"]'),
    "bank":          ('node["amenity"="bank"]', 'way["amenity"="bank"]', 'relation["amenity"="bank"]'),
    "school":        ('node["amenity"="school"]', 'way["amenity"="school"]', 'relation["amenity"="school"]'),
    "college":       ('node["amenity"="college"]', 'way["amenity"="college"]', 'relation["amenity"="college"]'),
    "university":    ('node["amenity"="university"]', 'way["amenity"="university"]', 'relation["amenity"="university"]'),
    "hotel":         ('node["tourism"="hotel"]', 'way["tourism"="hotel"]', 'relation["tourism"="hotel"]'),
    "restaurant":    ('node["amenity"="restaurant"]', 'way["amenity"="restaurant"]', 'relation["amenity"="restaurant"]'),
    "park":          ('node["leisure"="park"]', 'way["leisure"="park"]', 'relation["leisure"="park"]'),
}

# Politeness settings
SLEEP_BETWEEN_QUERIES = 1.2  # seconds


def query_overpass(q: str, timeout: int = 180) -> Dict:
    """Send a query to Overpass and return JSON. Raises on HTTP errors."""
    resp = requests.post(OVERPASS_URL, data=q.encode("utf-8"), timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def find_area_by_name(name: str) -> Optional[int]:
    """
    Try to find an OSM area id for a given place name.
    Returns Overpass 'area id' (which is relation/way id + 3600000000 for relations typically) or None.
    """
    # We ask Overpass to return area ids for matching administrative boundaries
    q = f"""
    [out:json][timeout:25];
    area["name"="{name}"]["boundary"="administrative"];
    out ids qt;
    """
    try:
        data = query_overpass(q)
    except Exception:
        return None
    elems = data.get("elements", [])
    if not elems:
        return None
    # return the first area's id
    return elems[0].get("id")


def build_overpass_query_for_area(area_id: int, clauses: List[str]) -> str:
    """
    Build a query that searches inside an Overpass area (area id).
    Use 'out center' for ways/relations to get lat/lon.
    """
    joined = ";\n  ".join(clauses)
    q = f"""
    [out:json][timeout:180];
    area({area_id})->.searchArea;
    (
      {joined}(area.searchArea);
    );
    out center tags;
    """
    return q


def build_overpass_query_for_bbox(bbox: Tuple[float,float,float,float], clauses: List[str]) -> str:
    """Build an Overpass query for a bounding box (south,west,north,east)."""
    s, w, n, e = bbox
    joined = ";\n  ".join(clauses)
    q = f"""
    [out:json][timeout:180];
    (
      {joined}({s},{w},{n},{e});
    );
    out center tags;
    """
    return q


def extract_coords(elem: Dict) -> Tuple[Optional[float], Optional[float]]:
    """Return (lat, lon) for node/way/relation element returned by Overpass."""
    typ = elem.get("type")
    if typ == "node":
        return elem.get("lat"), elem.get("lon")
    center = elem.get("center")
    if center:
        return center.get("lat"), center.get("lon")
    return None, None


def dedupe_rows(rows: List[Dict]) -> List[Dict]:
    """Deduplicate by (osm_type, osm_id). Keep first occurrence."""
    seen = set()
    out = []
    for r in rows:
        key = (r.get("osm_type"), r.get("osm_id"))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def tile_bbox(bbox: Tuple[float,float,float,float], tile_deg: float) -> List[Tuple[float,float,float,float]]:
    """Split bbox into tiles of degree size tile_deg and return list of (s,w,n,e)."""
    s0, w0, n0, e0 = bbox
    tiles = []
    lat = s0
    while lat < n0:
        lon = w0
        lat_n = min(lat + tile_deg, n0)
        while lon < e0:
            lon_e = min(lon + tile_deg, e0)
            tiles.append((lat, lon, lat_n, lon_e))
            lon += tile_deg
        lat += tile_deg
    return tiles


def run_scrape(use_tiling: bool = True) -> pd.DataFrame:
    rows = []

    # 1) Try area name candidates
    area_id = None
    for candidate in AREA_NAME_CANDIDATES:
        print(f"Trying area lookup for: {candidate}")
        aid = find_area_by_name(candidate)
        if aid:
            print(f"Found area id {aid} for '{candidate}' — using area search.")
            area_id = aid
            break
        time.sleep(0.6)

    # 2) Decide strategy: area search or bbox-tiling search
    if area_id:
        # Do a single area-based query per category
        for category, clauses in CATEGORIES.items():
            print(f"Querying category '{category}' inside area...")
            q = build_overpass_query_for_area(area_id, list(clauses))
            try:
                data = query_overpass(q)
            except Exception as e:
                print(f"  Error querying Overpass for {category}: {e}")
                continue
            for el in data.get("elements", []):
                lat, lon = extract_coords(el)
                tags = el.get("tags") or {}
                name = tags.get("name", "")
                rows.append({
                    "name": name,
                    "category": category,
                    "osm_type": el.get("type"),
                    "osm_id": el.get("id"),
                    "lat": lat,
                    "lon": lon,
                    "tags": str(tags),
                })
            time.sleep(SLEEP_BETWEEN_QUERIES)
    else:
        # Fallback: use bbox tiling (recommended if area lookup failed)
        print("Area lookup failed — falling back to bbox tiling for Greater Dhaka.")
        tiles = tile_bbox(FALLBACK_BBOX, TILE_DEG) if use_tiling else [FALLBACK_BBOX]
        print(f"Tiles to query: {len(tiles)} (tile size {TILE_DEG} deg).")
        for idx, tile in enumerate(tiles):
            s, w, n, e = tile
            print(f"Tile {idx+1}/{len(tiles)} -> s:{s}, w:{w}, n:{n}, e:{e}")
            for category, clauses in CATEGORIES.items():
                q = build_overpass_query_for_bbox(tile, list(clauses))
                try:
                    data = query_overpass(q)
                except Exception as exc:
                    print(f"  Error for tile {idx+1} category {category}: {exc}")
                    # small wait and continue
                    time.sleep(1.5)
                    continue
                for el in data.get("elements", []):
                    lat, lon = extract_coords(el)
                    tags = el.get("tags") or {}
                    name = tags.get("name", "")
                    rows.append({
                        "name": name,
                        "category": category,
                        "osm_type": el.get("type"),
                        "osm_id": el.get("id"),
                        "lat": lat,
                        "lon": lon,
                        "tags": str(tags),
                    })
                time.sleep(0.25)  # tiny pause between category queries within a tile
            # polite pause per tile
            time.sleep(SLEEP_BETWEEN_QUERIES)

    # Dedupe & cleanup
    print(f"Collected {len(rows)} raw items; deduplicating...")
    rows = dedupe_rows(rows)
    df = pd.DataFrame(rows, columns=["name","category","osm_type","osm_id","lat","lon","tags"])
    # drop coords-missing rows
    before = len(df)
    df = df.dropna(subset=["lat","lon"])
    after = len(df)
    print(f"After dropping missing coords: {after} items (dropped {before-after}).")
    return df


def save_to_excel(df: pd.DataFrame, filename: str = "dhaka_pois.xlsx"):
    if df.empty:
        print("No results to save.")
        return
    # main sheet
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="pois", index=False)
        # separate sheets per category
        for cat in sorted(df["category"].unique()):
            sub = df[df["category"] == cat]
            sub.to_excel(writer, sheet_name=cat[:31], index=False)  # Excel sheet name limit
    print(f"Saved {len(df)} POIs to {filename}")


def main():
    print("Starting robust Dhaka Overpass scrape...")
    df = run_scrape(use_tiling=True)
    save_to_excel(df)


if __name__ == "__main__":
    main()

