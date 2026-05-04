import asyncio
import aiohttp
import time

INPUT_M3U_URL = "https://iptv-org.github.io/iptv/languages/tur.m3u"

OUTPUT_FILE = "filtered.m3u"
README_FILE = "README.md"

TIMEOUT = aiohttp.ClientTimeout(total=10)
CONCURRENT_LIMIT = 80

MAX_RESPONSE_TIME = 4.0

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# -----------------------------
# FETCH M3U
# -----------------------------
async def fetch_m3u(session):
    async with session.get(INPUT_M3U_URL) as resp:
        resp.raise_for_status()
        text = await resp.text()
        return text.splitlines()

# -----------------------------
# PARSE
# -----------------------------
def parse_m3u(lines):
    pairs = []
    i = 0

    while i < len(lines):
        if lines[i].startswith("#EXTINF") and i + 1 < len(lines):
            pairs.append((lines[i], lines[i + 1]))
            i += 2
        else:
            i += 1

    return pairs

# -----------------------------
# HLS CHECK (soft)
# -----------------------------
async def check_hls(session, url):
    try:
        async with session.get(url, headers=HEADERS) as resp:
            if resp.status != 200:
                return False

            text = await resp.text()

            for line in text.splitlines():
                if line and not line.startswith("#"):
                    segment = line.strip()
                    break
            else:
                return False

        async with session.get(segment, headers=HEADERS) as seg:
            return seg.status == 200

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

                # HLS validation (soft)
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
# SAVE M3U
# -----------------------------
def save_m3u(pairs):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for extinf, url, _ in pairs:
            f.write(extinf + "\n")
            f.write(url + "\n")

# -----------------------------
# README
# -----------------------------
def update_readme(results):
    count = len(results)
    avg = sum(r[2] for r in results) / count if count else 0

    content = f"""# 🇹🇷 Turkish IPTV Filtered List

## 📊 Stats

- ✅ Working streams: **{count}**
- ⚡ Avg response time: **{avg:.2f}s**

## 🔄 Auto Update
Updated daily via GitHub Actions.

## 📡 Source
- iptv-org tur.m3u filtered with live validation
"""

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

# -----------------------------
# MAIN
# -----------------------------
async def main():
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:

        print("📥 Turkish playlist indiriliyor...")
        lines = await fetch_m3u(session)

        print("🔍 Parse ediliyor...")
        pairs = parse_m3u(lines)

        print(f"📺 Toplam TR kanal: {len(pairs)}")

        print("⚙️ Test ediliyor...")
        results = await filter_streams(session, pairs)

        print(f"✅ Çalışan: {len(results)}")

        save_m3u(results)
        update_readme(results)

        print("🎉 Bitti")

if __name__ == "__main__":
    asyncio.run(main())
