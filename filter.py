import asyncio
import aiohttp
import time

INPUT_M3U_URL = "https://iptv-org.github.io/iptv/index.m3u"
OUTPUT_FILE = "filtered.m3u"
README_FILE = "README.md"

TIMEOUT = aiohttp.ClientTimeout(total=8)
CONCURRENT_LIMIT = 80
MAX_RESPONSE_TIME = 1.5  # saniye

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# --- M3U indir ---
async def fetch_m3u(session):
    async with session.get(INPUT_M3U_URL) as resp:
        resp.raise_for_status()
        text = await resp.text()
        return text.splitlines()

# --- parse ---
def parse_m3u(lines):
    pairs = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF") and i + 1 < len(lines):
            pairs.append((line, lines[i + 1]))
            i += 2
        else:
            i += 1

    return pairs

# --- TR filtresi ---
def is_tr_channel(extinf):
    return 'tvg-country="TR"' in extinf or 'group-title="Turkey"' in extinf

# --- HLS segment test ---
async def check_hls(session, url):
    try:
        async with session.get(url, headers=HEADERS) as resp:
            if resp.status != 200:
                return False

            text = await resp.text()

            # ilk segmenti bul
            for line in text.splitlines():
                if line and not line.startswith("#"):
                    segment_url = line
                    break
            else:
                return False

        # segment çek
        async with session.get(segment_url, headers=HEADERS) as seg:
            return seg.status == 200

    except:
        return False

# --- stream test ---
async def check_stream(session, sem, extinf, url):
    if not is_tr_channel(extinf):
        return None

    async with sem:
        start = time.perf_counter()

        try:
            async with session.get(url, headers=HEADERS) as resp:
                if resp.status != 200:
                    return None

                elapsed = time.perf_counter() - start

                if elapsed > MAX_RESPONSE_TIME:
                    return None

                # HLS kontrol
                if ".m3u8" in url:
                    ok = await check_hls(session, url)
                    if not ok:
                        return None

                return (extinf, url, elapsed)

        except:
            return None

# --- filtre ---
async def filter_streams(session, pairs):
    sem = asyncio.Semaphore(CONCURRENT_LIMIT)

    tasks = [
        check_stream(session, sem, extinf, url)
        for extinf, url in pairs
    ]

    results = await asyncio.gather(*tasks)
    return [r for r in results if r]

# --- kaydet ---
def save_m3u(pairs):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for extinf, url, _ in pairs:
            f.write(extinf + "\n")
            f.write(url + "\n")

# --- README güncelle ---
def update_readme(count, avg_speed):
    content = f"""# IPTV Filtered List

## 📊 Güncel İstatistikler

- ✅ Çalışan kanal sayısı: **{count}**
- ⚡ Ortalama yanıt süresi: **{avg_speed:.2f} sn**

## 🔄 Otomatik Güncelleme
Bu liste her gün GitHub Actions ile güncellenir.
"""

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

# --- main ---
async def main():
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        lines = await fetch_m3u(session)
        pairs = parse_m3u(lines)

        results = await filter_streams(session, pairs)

        if results:
            avg_speed = sum(r[2] for r in results) / len(results)
        else:
            avg_speed = 0

        save_m3u(results)
        update_readme(len(results), avg_speed)

if __name__ == "__main__":
    asyncio.run(main())