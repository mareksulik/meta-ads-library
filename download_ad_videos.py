#!/usr/bin/env python3
"""Download videos from Facebook Ads Library by Library ID."""

import argparse
import sys
from pathlib import Path


def download_via_ytdlp(library_id: str, output_dir: Path, quality: str) -> list[Path]:
    """Download ad video(s) using yt-dlp's built-in Facebook Ads extractor."""
    import yt_dlp

    url = f"https://www.facebook.com/ads/library/?id={library_id}"
    downloaded = []

    format_map = {
        "best": "bestvideo+bestaudio/best",
        "hd": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "sd": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    }

    def progress_hook(d):
        if d["status"] == "finished":
            path = Path(d.get("info_dict", {}).get("filepath", d.get("filename", "")))
            if path.exists():
                downloaded.append(path)

    opts = {
        "format": format_map.get(quality, format_map["best"]),
        "outtmpl": str(output_dir / f"{library_id}_%(playlist_index|0)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception:
        pass  # yt-dlp may error on post-download requests even if file was saved

    # Progress hook may miss files if yt-dlp errors mid-session; scan output dir
    if not downloaded:
        downloaded = list(output_dir.glob(f"{library_id}_*"))

    return downloaded


def download_via_playwright(library_id: str, output_dir: Path) -> list[Path]:
    """Fallback: use headless browser to intercept video URLs."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Install with: pip install playwright && playwright install chromium")
        return []

    import httpx

    url = f"https://www.facebook.com/ads/library/?id={library_id}"
    video_urls: set[str] = set()

    def handle_response(response):
        content_type = response.headers.get("content-type", "")
        if "video" in content_type and response.url not in video_urls:
            video_urls.add(response.url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("response", handle_response)
        page.goto(url, wait_until="networkidle", timeout=30000)

        # Also check <video> src attributes in DOM
        for src in page.eval_on_selector_all("video source, video", """
            els => els.map(e => e.src || e.getAttribute('src')).filter(Boolean)
        """):
            if src and src.startswith("http"):
                video_urls.add(src)

        browser.close()

    downloaded = []
    with httpx.Client(follow_redirects=True, timeout=60) as client:
        for i, video_url in enumerate(video_urls):
            dest = output_dir / f"{library_id}_{i}.mp4"
            resp = client.get(video_url)
            if resp.status_code == 200 and len(resp.content) > 1000:
                dest.write_bytes(resp.content)
                downloaded.append(dest)
                print(f"  Downloaded: {dest.name} ({len(resp.content) / 1024:.0f} KB)")

    return downloaded


def download_ad(library_id: str, output_dir: Path, quality: str, method: str) -> list[Path]:
    """Orchestrate download: try yt-dlp first, fall back to Playwright."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if method in ("auto", "ytdlp"):
        files = download_via_ytdlp(library_id, output_dir, quality)
        if files:
            return files
        if method == "ytdlp":
            print(f"  yt-dlp: no video found for {library_id}")
            return []
        print(f"  yt-dlp found nothing, trying Playwright...")

    if method in ("auto", "playwright"):
        try:
            return download_via_playwright(library_id, output_dir)
        except Exception as e:
            print(f"  Playwright failed: {e}")

    return []


def main():
    parser = argparse.ArgumentParser(description="Download videos from Facebook Ads Library")
    parser.add_argument("library_ids", nargs="+", help="One or more Ad Library IDs")
    parser.add_argument("-o", "--output-dir", default="./downloads", help="Output directory (default: ./downloads)")
    parser.add_argument("-m", "--method", choices=["auto", "ytdlp", "playwright"], default="auto",
                        help="Download method (default: auto)")
    parser.add_argument("-q", "--quality", choices=["best", "hd", "sd"], default="best",
                        help="Video quality (default: best)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    total_files = []

    for lib_id in args.library_ids:
        print(f"[{lib_id}] Downloading...")
        files = download_ad(lib_id, output_dir, args.quality, args.method)
        if files:
            for f in files:
                print(f"  ✓ {f}")
            total_files.extend(files)
        else:
            print(f"  No video found for {lib_id}")

    print(f"\nDone: {len(total_files)} file(s) downloaded to {output_dir}/")
    return 0 if total_files else 1


if __name__ == "__main__":
    sys.exit(main())
