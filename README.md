# 📺 Mytv - M3U Stream Filter & Validator

## ✨ Overview

Mytv is a powerful Python script designed to manage and validate M3U (IPTV) playlists. It automates the process of consolidating multiple M3U sources, removing duplicates, checking stream availability and responsiveness, and ensuring HLS streams are functional. The output is a clean, sorted, and validated `filtered.m3u` playlist ready for use with your favorite media player.

## 🚀 Features

-   **Multi-Source Merging:** Combines streams from various `sources.txt` entries into a single, comprehensive list.
-   **Duplicate Stream Removal:** Intelligently identifies and eliminates redundant stream URLs, ensuring a unique playlist.
-   **Intelligent Stream Validation:**
    -   **Response Time Filtering:** Filters out streams that are too slow, keeping only those responding within `4.0s`.
    -   **HLS Stream Health Check:** Performs a strict validation for HLS (`.m3u8`) streams by attempting to fetch the main playlist and its first segment, ensuring they are truly live and accessible.
-   **Alphabetical Sorting:** Organizes the final playlist alphabetically by channel name for easy navigation.
-   **Automated Reporting:** Generates a `README.md` with real-time statistics on stream health and performance.

##  Current Statistics

-   📥 Total input streams processed: **1706**
-   ✅ Working and validated streams: **635**
-   ⚡ Average response time for working streams: **0.52s**

## ⚙️ How to Use

1.  **Populate `sources.txt`:** Add the URLs of your M3U playlists, one URL per line.
2.  **Run the script:** Execute `python xdxd.py` (or your script name).
3.  **Get `filtered.m3u`:** A new `filtered.m3u` file will be generated in the same directory, containing all the validated and optimized streams.

## 🔗 Download Your Filtered M3U List

Click here to download the latest `filtered.m3u` playlist

