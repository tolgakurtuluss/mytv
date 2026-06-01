import asyncio
import aiohttp
import time

import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SOURCE_FILE = "sources.txt"
OUTPUT_FILE = "filtered.m3u"
README_FILE = "README.md"

GLOBAL_CLIENT_TIMEOUT = aiohttp.ClientTimeout(total=10) # Total timeout for the aiohttp client session
HLS_SEGMENT_CHECK_TIMEOUT = 5.0 # Timeout for fetching HLS playlist and its first segment
CONCURRENT_LIMIT = 80
MAX_RESPONSE_TIME = 4.0
HEADERS = {"User-Agent": "Mozilla/5.0"}

# -----------------------------
# SOURCES LOAD
# -----------------------------
def load_sources():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

# -----------------------------
# FETCH M3U
# -----------------------------
async def fetch_m3u(session, url):
    async with session.get(url) as resp:
        resp.raise_for_status()
        return (await resp.text()).splitlines()

# -----------------------------
# PARSE
# -----------------------------
def parse_m3u(lines):
    pairs = []
    i = 0

    while i < len(lines):
        if lines[i].startswith("#EXTINF") and i + 1 < len(lines):
            extinf = lines[i].strip()
            url = lines[i + 1].strip()
            pairs.append((extinf, url))
            i += 2
        else:
            i += 1

    return pairs

# -----------------------------
# DEDUP
# -----------------------------
def dedup(pairs):
    seen = set()
    out = []

    for extinf, url in pairs:
        if url not in seen:
            seen.add(url)
            out.append((extinf, url))

    return out

# -----------------------------
# CHANNEL NAME
# -----------------------------
def extract_name(extinf):
    name = ""
    if "," in extinf:
        name = extinf.split(",")[-1].strip()
    else:
        name = extinf.strip()

    # Handle parenthesis truncation
    if "(" in name:
        name = name.split("(", 1)[0].strip()

    # Convert to uppercase
    return name.upper()

# -----------------------------
# HLS CHECK (strict)
# -----------------------------
async def check_hls(session, url):
    """
    Performs a strict HLS check by attempting to fetch the playlist and its first segment.
    """
    try:
        # Fetch the HLS playlist
        async with session.get(url, headers=HEADERS, timeout=HLS_SEGMENT_CHECK_TIMEOUT) as resp:
            if resp.status != 200:
                logging.info(f"HLS playlist check failed for {url} with status {resp.status}") # Covers 301, 403, etc.
                return False
            
            text = await resp.text()
            
            segment = None
            for line in text.splitlines():
                # Find the first non-comment, non-empty line which should be a segment or another playlist
                if line and not line.startswith("#"):
                    segment = line.strip()
                    break
            
            if not segment:
                logging.info(f"No segments found in HLS playlist for {url}")
                return False
            # Segment URL tam URL değilse (relative ise) ana URL ile birleştir
            if not segment.startswith("http"):
                segment = urljoin(url, segment)
            
            # Fetch the first segment
            async with session.get(segment, headers=HEADERS, timeout=HLS_SEGMENT_CHECK_TIMEOUT) as r:
                if r.status != 200: # Covers 301, 403, etc.
                    logging.info(f"HLS segment check failed for {segment} (from {url}) with status {r.status}")
                    return False
                return True

    except asyncio.TimeoutError:
        logging.debug(f"HLS check timed out for {url} or its segment after {HLS_SEGMENT_CHECK_TIMEOUT}s")
        return False
    except aiohttp.ClientError as e:
        logging.debug(f"HLS client error for {url}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during HLS check for {url}: {e}")
        return False

# -----------------------------
# STREAM CHECK
# -----------------------------
async def check_stream(session, sem, extinf, url):
    """
    Checks if a stream is live and responsive within MAX_RESPONSE_TIME.
    Performs an HLS check if the URL is an M3U8 playlist.
    """
    async with sem:
        start = time.perf_counter()
        
        try:
            # Use the session's default timeout (GLOBAL_CLIENT_TIMEOUT) for the initial request
            async with session.get(url, headers=HEADERS) as resp:
                final_url = str(resp.url)
                redirect_info = ""
                if resp.history:
                    redirect_info = f" (redirected from {url} to {final_url})"

                if resp.status != 200: # Covers 301, 403, etc.
                    logging.info(f"Stream check failed for {final_url} with status {resp.status}{redirect_info}")
                    return None
                elapsed = time.perf_counter() - start
                if elapsed > MAX_RESPONSE_TIME:
                    logging.info(f"Stream {url} too slow: {elapsed:.2f}s > {MAX_RESPONSE_TIME}s")
                    return None
                if ".m3u8" in url:
                    logging.debug(f"Performing HLS check for {url}")
                    if not await check_hls(session, url):
                        logging.info(f"HLS validation failed for {url}")
                        return None

                logging.info(f"Stream {final_url} is working. Response time: {elapsed:.2f}s{redirect_info}")
                return (extinf, url, elapsed)
        except asyncio.TimeoutError:
            logging.info(f"Stream check timed out for {url} after {GLOBAL_CLIENT_TIMEOUT.total}s (initial URL)")
            return None
        except aiohttp.ClientError as e:
            logging.info(f"Stream client error for {url} (initial URL): {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during stream check for {url} (initial URL): {e}")
            return None

# -----------------------------
# FILTER
# -----------------------------
async def filter_streams(session, pairs):
    sem = asyncio.Semaphore(CONCURRENT_LIMIT)

    tasks = [
        check_stream(session, sem, extinf, url)
        for extinf, url in pairs
    ]

    results = await asyncio.gather(*tasks)
    return [r for r in results if r]

# -----------------------------
# SAVE (ALPHABETICAL SORT)
# -----------------------------
def save_m3u(pairs):
    enriched = []

    for original_extinf, url, speed in pairs:
        # Get the modified channel name (uppercase and truncated)
        modified_channel_name = extract_name(original_extinf)

        # Reconstruct the extinf line with the modified channel name
        last_comma_index = original_extinf.rfind(',')
        if last_comma_index != -1:
            # Replace the old channel name with the modified one
            new_extinf = original_extinf[:last_comma_index + 1] + modified_channel_name
        else:
            # If no comma, the whole extinf is the name, so just use the modified name
            new_extinf = modified_channel_name

        enriched.append((modified_channel_name.lower(), new_extinf, url, speed))

    # 🔤 A → Z SORT
    enriched.sort(key=lambda x: x[0])
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write('#EXTM3U x-tvg-url="http://epg.siptveu.com/epg/guide-turkey.xml.gz"' + "\n")

        for _, extinf, url, _ in enriched:
            f.write(extinf + "\n")
            f.write(url + "\n")

# -----------------------------
# README
# -----------------------------
def update_readme(results, total_input):
    count = len(results)
    avg = sum(r[2] for r in results) / count if count else 0

    content = f"""# 📺 Mytv - M3U Stream Filter & Validator

## ✨ Overview

Mytv is a powerful Python script designed to manage and validate M3U (IPTV) playlists. It automates the process of consolidating multiple M3U sources, removing duplicates, checking stream availability and responsiveness, and ensuring HLS streams are functional. The output is a clean, sorted, and validated `filtered.m3u` playlist ready for use with your favorite media player.

## 🚀 Features

-   **Multi-Source Merging:** Combines streams from various `sources.txt` entries into a single, comprehensive list.
-   **Duplicate Stream Removal:** Intelligently identifies and eliminates redundant stream URLs, ensuring a unique playlist.
-   **Intelligent Stream Validation:**
    -   **Response Time Filtering:** Filters out streams that are too slow, keeping only those responding within `{MAX_RESPONSE_TIME}s`.
    -   **HLS Stream Health Check:** Performs a strict validation for HLS (`.m3u8`) streams by attempting to fetch the main playlist and its first segment, ensuring they are truly live and accessible.
-   **Alphabetical Sorting:** Organizes the final playlist alphabetically by channel name for easy navigation.
-   **Automated Reporting:** Generates a `README.md` with real-time statistics on stream health and performance.

##  Current Statistics

-   📥 Total input streams processed: **{total_input}**
-   ✅ Working and validated streams: **{count}**
-   ⚡ Average response time for working streams: **{avg:.2f}s**

## ⚙️ How to Use

1.  **Populate `sources.txt`:** Add the URLs of your M3U playlists, one URL per line.
2.  **Run the script:** Execute `python xdxd.py` (or your script name).
3.  **Get `filtered.m3u`:** A new `filtered.m3u` file will be generated in the same directory, containing all the validated and optimized streams.

## 🔗 Download Your Filtered M3U List

Click here to download the latest `filtered.m3u` playlist

"""
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

# -----------------------------
# MAIN
# -----------------------------
async def main():
    sources = load_sources()

    async with aiohttp.ClientSession(timeout=GLOBAL_CLIENT_TIMEOUT) as session:

        print(f"📡 Sources: {len(sources)}")

        all_pairs = []

        for url in sources:
            print(f"📥 Fetch: {url}")
            lines = await fetch_m3u(session, url)
            all_pairs.extend(parse_m3u(lines))

        print(f"📺 Raw: {len(all_pairs)}")

        print("🧹 Dedup...")
        all_pairs = dedup(all_pairs)

        print(f"📺 Unique: {len(all_pairs)}")

        print("⚙️ Filtering...")
        results = await filter_streams(session, all_pairs)

        print(f"✅ Working: {len(results)}")

        save_m3u(results)
        update_readme(results, len(all_pairs))

        print("🎉 Done")

if __name__ == "__main__":
    asyncio.run(main())
    
