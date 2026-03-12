# Meta Ads Library Video Downloader

Python CLI tool to download videos from Facebook Ad Library by Library ID.

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Single ad
python download_ad_videos.py 944405094827445

# Multiple ads
python download_ad_videos.py 944405094827445 786737104443670 1280488330594936

# Custom output directory
python download_ad_videos.py 944405094827445 -o ./videos

# Lower quality
python download_ad_videos.py 944405094827445 -q sd

# Force Playwright fallback
python download_ad_videos.py 944405094827445 -m playwright
```

## Options

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `-o, --output-dir` | path | `./downloads` | Output directory |
| `-m, --method` | `auto`, `ytdlp`, `playwright` | `auto` | Download method |
| `-q, --quality` | `best`, `hd`, `sd` | `best` | Video quality |

## How it works

1. **Primary method (yt-dlp)** — uses yt-dlp's built-in `FacebookAdsIE` extractor. Handles carousel ads (multiple videos) automatically.
2. **Fallback (Playwright)** — headless Chromium intercepts video URLs from network traffic. Requires separate install: `pip install playwright && playwright install chromium`

The `auto` method tries yt-dlp first, falls back to Playwright if no videos are found.

## Finding Library IDs

Go to [Facebook Ad Library](https://www.facebook.com/ads/library/), search for an ad, and copy the ID from the URL:

```
https://www.facebook.com/ads/library/?id=944405094827445
                                         ^^^^^^^^^^^^^^^
                                         This is the Library ID
```
