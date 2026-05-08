<<<<<<< HEAD
import asyncio
import aiohttp
import time

SOURCE_FILE = "sources.txt"

OUTPUT_FILE = "filtered.m3u"
README_FILE = "README.md"

TIMEOUT = aiohttp.ClientTimeout(total=10)
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
    if "," in extinf:
        return extinf.split(",")[-1].strip()
    return extinf.strip()

# -----------------------------
# HLS CHECK (strict)
# -----------------------------
async def check_hls(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=5) as resp:
            if resp.status != 200:
                return False

            text = await resp.text()

            segment = None
            for line in text.splitlines():
                if line and not line.startswith("#"):
                    segment = line.strip()
                    break

            if not segment:
                return False

            # Segment URL tam URL değilse (relative ise) ana URL ile birleştir
            if not segment.startswith("http"):
                from urllib.parse import urljoin
                segment = urljoin(url, segment)

        async with session.get(segment, headers=HEADERS, timeout=5) as r:
            return r.status == 200

    except:
        return False  # Hata varsa kanal çalışmıyordur, listeye alma

# -----------------------------
# STREAM CHECK
# -----------------------------
async def check_stream(session, sem, extinf, url):
    async with sem:
        start = time.perf_counter()

        try:
            async with session.get(url, headers=HEADERS) as resp:
                if resp.status != 200:
                    return None

                elapsed = time.perf_counter() - start

                if elapsed > MAX_RESPONSE_TIME:
                    return None

                if ".m3u8" in url:
                    try:
                        ok = await check_hls(session, url)
                        if not ok:
                            return None
                    except:
                        pass

                return (extinf, url, elapsed)

        except:
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

    for extinf, url, speed in pairs:
        name = extract_name(extinf)
        enriched.append((name.lower(), extinf, url, speed))

    # 🔤 A → Z SORT
    enriched.sort(key=lambda x: x[0])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for _, extinf, url, _ in enriched:
            f.write(extinf + "\n")
            f.write(url + "\n")

# -----------------------------
# README
# -----------------------------
def update_readme(results, total_input):
    count = len(results)
    avg = sum(r[2] for r in results) / count if count else 0

    content = f"""# 📺 IPTV Filter Engine

## 📊 Stats

- 📥 Input streams: **{total_input}**
- ✅ Working streams: **{count}**
- ⚡ Avg response time: **{avg:.2f}s**

## ⚙️ Features
- Multi-source merge
- Duplicate removal
- Speed filtering (< {MAX_RESPONSE_TIME}s)
- HLS validation (soft fail)
- Alphabetical sorting (A → Z)

## 🔄 Sources
Loaded from `sources.txt`
"""

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

# -----------------------------
# MAIN
# -----------------------------
async def main():
    sources = load_sources()

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:

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
=======
import asyncio
import aiohttp
import time

SOURCE_FILE = "sources.txt"

OUTPUT_FILE = "filtered.m3u"
README_FILE = "README.md"

TIMEOUT = aiohttp.ClientTimeout(total=10)
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
    if "," in extinf:
        return extinf.split(",")[-1].strip()
    return extinf.strip()

# -----------------------------
# HLS CHECK (soft)
# -----------------------------
async def check_hls(session, url):
    try:
        async with session.get(url, headers=HEADERS) as resp:
            if resp.status != 200:
                return False

            text = await resp.text()

            segment = None
            for line in text.splitlines():
                if line and not line.startswith("#"):
                    segment = line.strip()
                    break

            if not segment:
                return False

        async with session.get(segment, headers=HEADERS) as r:
            return r.status == 200

    except:
        return True  # soft fail

# -----------------------------
# STREAM CHECK
# -----------------------------
async def check_stream(session, sem, extinf, url):
    async with sem:
        start = time.perf_counter()

        try:
            async with session.get(url, headers=HEADERS) as resp:
                if resp.status != 200:
                    return None

                elapsed = time.perf_counter() - start

                if elapsed > MAX_RESPONSE_TIME:
                    return None

                if ".m3u8" in url:
                    try:
                        ok = await check_hls(session, url)
                        if not ok:
                            return None
                    except:
                        pass

                return (extinf, url, elapsed)

        except:
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

    for extinf, url, speed in pairs:
        name = extract_name(extinf)
        enriched.append((name.lower(), extinf, url, speed))

    # 🔤 A → Z SORT
    enriched.sort(key=lambda x: x[0])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for _, extinf, url, _ in enriched:
            f.write(extinf + "\n")
            f.write(url + "\n")

# -----------------------------
# README
# -----------------------------
def update_readme(results, total_input):
    count = len(results)
    avg = sum(r[2] for r in results) / count if count else 0

    content = f"""# 📺 IPTV Filter Engine

## 📊 Stats

- 📥 Input streams: **{total_input}**
- ✅ Working streams: **{count}**
- ⚡ Avg response time: **{avg:.2f}s**

## ⚙️ Features
- Multi-source merge
- Duplicate removal
- Speed filtering (< {MAX_RESPONSE_TIME}s)
- HLS validation (soft fail)
- Alphabetical sorting (A → Z)

## 🔄 Sources
Loaded from `sources.txt`
"""

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

# -----------------------------
# MAIN
# -----------------------------
async def main():
    sources = load_sources()

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:

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
>>>>>>> de844d210a422bf4cd611e27f11e5a3090aa7161
